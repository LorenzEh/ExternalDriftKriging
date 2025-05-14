# External Drift Kriging ![Python](https://img.shields.io/badge/Python-3.8-blue.svg)

During my master's thesis, I began exploring various techniques for missing data estimation. As I delved deeper into geostatistics, I came across variography and kriging interpolation. 
While (spatially) analyzing key variables—such as county-level abortion rates and distances to abortion clinics across the contiguous United States—I realized that incorporating spatial information into the imputation process might improve accuracy.

After experimenting with different kriging methods and libraries—including Poisson kriging for rate-based data and block kriging to account for areal units—I found that the GSTools library provided the most reliable and flexible results. 
One of its key advantages was the seamless integration of the Matérn-Yadrenko variogram model, which accounts for the complex (heterogenous) spatial structure of the data and non-stationarity. 

Moreover, GSTools allowed for the inclusion of external drift variables (hence the name "External Drift Kriging", EDK), such as the distance to the nearest abortion provider—a variable that not shares a similar (negativley-correlated) spatial structure with abortion rates (i.e., greater distances are generally associated with lower abortion rates). 
The library also supported conditioning, which helped preserve local variance, especially in sparsely sampled areas. Without this, kriging estimates tend to regress toward the mean in regions with distant neighbors.

While collapsing county-level data to geometric centroids for kriging—and subsequently treating the interpolated point data as areal data for further analysis—is certainly an experimental approach, cross-validation demonstrated its robustness, particularly for neighboring counties. 
To validate the EDK results, I performed repeated random cross-validations: after setting a random seed, I excluded the abortion rate data for 100 randomly selected counties, applied EDK, and compared the interpolated values to the actual observations. 
Due to computational limitations, this process was repeated 100 times, yielding a mean correlation of 0.73 (ranging from 0.43 in the far field to 0.88 for missing data with close neighbours). 

These results suggest that EDK is particularly effective at interpolating values near observed data points, though its performance diminishes in more isolated regions.
