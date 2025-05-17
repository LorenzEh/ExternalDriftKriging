# External Drift Kriging ![Python](https://img.shields.io/badge/Python-3.8-blue.svg)

During my master's thesis, I began exploring various techniques for missing data estimation. As I delved deeper into geostatistics, I came across variography and kriging interpolation. 
While analyzing spatially autocorrelated key variables—such as county-level abortion rates and distances to abortion clinics across the contiguous United States—I realized that incorporating spatial information into the imputation process might improve accuracy.

After experimenting with different kriging methods and libraries—including Poisson kriging for rate-based data and block kriging to account for areal units—I found that the GSTools library provided the most reliable and flexible results. 
One of its key advantages was the seamless integration of the Matérn-Yadrenko variogram model, which accounts for the complex (heterogenous) spatial structure of the data and non-stationarity. 

Moreover, GSTools allowed for the inclusion of external drift variables (hence the name "External Drift Kriging", EDK), such as the distance to the nearest abortion provider—a variable that shares a similar (negativley-correlated) spatial structure with abortion rates (i.e., greater distances are generally associated with lower abortion rates). 
The library also supported conditioning, which helped preserve local variance, especially in sparsely sampled areas. Without this, kriging estimates tend to regress toward the mean in regions with distant neighbors.

While collapsing county-level data to geometric centroids for kriging—and subsequently treating the interpolated point data as areal data for further analysis—is certainly an experimental approach, cross-validation demonstrated its robustness, particularly for neighboring counties. 
To validate the EDK results, I performed repeated random cross-validations: after setting a random seed, I excluded the abortion rate data for 100 randomly selected counties, applied EDK, and compared the interpolated values to the actual observations. 
Due to computational limitations, this process was repeated 100 times, yielding a mean correlation of 0.73 (ranging from 0.43 in the far field to 0.88 for missing data with close neighbours). 

These results suggest that EDK is particularly effective at interpolating values near observed data points, though its performance diminishes in more isolated regions.


## **Description & Functionality**

This function takes a GeoPandas DataFrame containing spatial units and a target variable with missing values. It fits a variogram model to capture the spatial autocorrelation of the target variable. By leveraging the information from one or two external drift variables (auxiliary spatial covariates), it performs kriging to estimate the missing values. To account for the inherent uncertainty in spatial predictions, especially in areas with sparse data, the function generates multiple conditional random field realizations. These simulations honor the observed data and the spatial structure, providing a range of plausible spatial distributions.

#### *Key functionalities include:*

1. **Variogram Modeling:** Fitting a user-specified covariance model (e.g., Matérn) to the empirical spatial structure of the target variable.
2. **External Drift Kriging:** Utilizing one or two external drift variables to improve the accuracy of spatial interpolation.
3. **Conditional Simulations:** Generating multiple realizations of the spatial field, conditioned on the observed data and drift variables, to model prediction uncertainty.
4. **GeoPandas Integration:** Accepting and returning GeoDataFrames, ensuring seamless integration with spatial data workflows.
5. **Log-Normal Transformation:** Applying a log-normal transformation to the target variable to handle potential skewness.

## **`geokrig` Function**

### *What can be done with it:*

- Impute missing values in a spatial variable using external drift kriging.
- Incorporate auxiliary spatial covariates to enhance prediction accuracy.
- Generate multiple conditional simulations to assess and visualize spatial prediction uncertainty.
- Preserve the spatial variability of the target variable in the simulated fields.
- Output a Pandas DataFrame containing multiple conditional simulation realizations for each spatial unit.

### *Parameters:*

- `df`: `GeoDataFrame`
    - A GeoPandas DataFrame containing polygon geometries, the target variable, and one or two drift variables.
- `variable`: `str`
    - Name of the column in `df` to be interpolated. This column must contain missing values.
- `iterations`: `int`
    - The number of conditional simulations (random fields) to generate.
- `model`: `gstools.CovModel`
    - A GSTools covariance model class (e.g., `gs.Matern`) to be used for variogram fitting.
- `drift1`: `str`
    - Name of the primary external drift variable column in `df`.
- `drift2`: `str`, optional
    - Name of a secondary external drift variable column in `df`. Defaults to `None`.

### *Returns:*

- `fields_df`: `pandas.DataFrame`
    - A DataFrame where each row corresponds to a spatial unit, and each column represents one of the conditional simulation realizations.

### *Example Usage:*

```python

# Perform external drift kriging with 1000 conditional simulations
fields_df = geokrig(df=gdf,
                    variable="abortion_rate",
                    iterations=1000,
                    model=matern_model,
                    drift1="distance_to_clinic",
                    drift2="poverty_rate")
