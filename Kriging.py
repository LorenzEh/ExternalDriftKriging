def geokrig(df, variable, iterations, model, drift1, drift2=None): 
    
    """
    Perform external drift kriging (EDK) on spatial data with optional secondary drift variable 
    and generate conditional simulations to account for uncertainty in spatial predictions.

    This function:
    - Fits a variogram model (e.g., Matérn-Yadrenko) to the empirical spatial structure of a variable of interest.
    - Uses external drift kriging to estimate missing values, leveraging auxiliary spatially structured covariates.
    - Generates multiple conditional random fields to preserve spatial variability, especially in sparsely sampled areas.

    Parameters
    ----------
    df : GeoDataFrame
        A GeoPandas DataFrame containing geometries (typically polygons), the target variable, 
        and one or two drift variables.
    
    variable : str
        Name of the column in `df` to be interpolated (e.g., abortion rate). Must contain missing values to be imputed.

    iterations : int
        Number of conditional simulations (random fields) to generate for uncertainty modeling.

    model : gstools.CovModel
        A GSTools covariance model class (e.g., `gs.Matern`) to be used for variogram fitting.

    drift1 : str
        Name of the primary external drift variable (e.g., distance to nearest abortion clinic).

    drift2 : str, optional
        Name of a secondary external drift variable. If provided, both drift variables are used in kriging.

    Returns
    -------
    fields_df : pandas.DataFrame
        A DataFrame where each row corresponds to a spatial unit (e.g., a county), and each column is one of the 
        `iterations` conditional simulation realizations. These fields incorporate spatial uncertainty and can 
        be used for downstream analysis or validation.
    
    Notes
    -----
    - The function assumes `df` contains a valid `geometry` column with polygon geometries.
    - Geometries are reduced to centroids for kriging, and the output is mapped back to the areal units.
    - The target variable is normalized using a log-normal transformation.
    - Variogram estimation uses Cressie’s robust estimator, and kriging operates on an unstructured mesh.
    - This implementation supports kriging with external drift and simulates realistic spatial fields by conditioning 
      on observed values and auxiliary covariates.

    Example
    -------
    fields_df = geokrig(df=my_geodataframe,
                        variable="abortion_rate",
                        iterations=100,
                        model=gs.Matern,
                        drift1="distance_to_clinic",
                        drift2="poverty_rate")
    """
    
    intpoints = df[~df[variable].isnull()]
    intpoints.reset_index(drop=True, inplace=True)
    
    # collapse the areas (counties) to their geometrical centroids
    lat = intpoints["geometry"].geometry.centroid.x
    lon = intpoints["geometry"].geometry.centroid.y  
    int_data = intpoints[variable].values
    
    # drift data
    g_lat = df["geometry"].geometry.centroid.x
    g_lon = df["geometry"].geometry.centroid.y
    
    external_drift_data1 = df[drift1].values

    if drift2 is not None:
        external_drift_data2 = df[drift2].values  
        external_drift_data = np.vstack((external_drift_data1, external_drift_data2))
        
        external_drift_at_abortion1 = intpoints[drift1].values
        external_drift_at_abortion2 = intpoints[drift2].values 
        external_drift_at_abortion = np.vstack((external_drift_at_abortion1, external_drift_at_abortion2))
    else:
        external_drift_data = external_drift_data1
        external_drift_at_abortion = intpoints[drift1].values

    # we introduce the LogNormal workflow, as abortion data follows a logarithmic distribution
    normalizer = gs.normalizer.LogNormal(int_data) 

    bin_center, vario = gs.vario_estimate(
                        (lat, lon), 
                        int_data, 
                        estimator = "cressie", 
                        latlon=True, 
                        mesh_type="unstructured", # unstructured mesh type to account for irregular shapes of counties
                        normalizer=normalizer)             
                        
    print("estimated bin number:", len(bin_center))
    print("maximal bin distance:", max(bin_center))
    
    # fit the model (Yadrenko)
    model = model(dim = 2, latlon=True) # covariance model with 2 dimensions (latlong = True, means that we're using a degree scale, therefore: Matern Yadrenko model)
    model.fit_variogram(bin_center, vario, nugget = False, loss = "cauchy")  # cauchy loss function
    
    # plotting:
    ax = model.plot("vario_yadrenko", x_max=max(bin_center)) 
    ax.scatter(bin_center, vario)
    ax.legend(fontsize='x-large')
    print(model)
    
    # kriging:
    krig = gs.krige.ExtDrift(model = model, 
                             cond_pos = (lat, lon), 
                             cond_val = int_data,
                             ext_drift = external_drift_at_abortion)

    krig.unstructured((g_lat, g_lon), ext_drift = external_drift_data, chunk_size = 100)
    

    krig(return_var=True, store="krig", ext_drift = external_drift_data) 
    krig(only_mean=True, store="mean_field", ext_drift = external_drift_data) 
    
    
    cond_srf = gs.CondSRF(krige = krig, 
                          latlon = True) 
    
    cond_srf.set_pos(pos = (g_lat, g_lon), 
                     mesh_type = "unstructured")
    
    # generate random fields to  account for variance in the far field
    seed = gs.random.MasterRNG(20170519)
    fields = {} 
    
    for i in range(iterations):
        cond_srf(seed=seed(), store=[f"f{i}", False, False], ext_drift = external_drift_data)
        fields[f"field_{i}"] = cond_srf[f"f{i}"]
        print("_____________")
        print("Interation:", i)
        
    fields = [cond_srf[f"f{i}"] for i in range(iterations)]
    
          
    df["cond_krig"] = krig["krig"]   
    fields_df = pd.DataFrame(fields)
    fields_df = fields_df.T.reset_index(drop=True)
    
    return fields_df
