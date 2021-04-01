# work-resumprion
  Estimating the level of work resumption in some Chinese cities in 2020 using NPP-VIIRS nighttime light remote sensing data
# Introduction
  hdf_to_tif_VIIRS.py：Convert daily nighttime lights data and MODIS surface reflectance data from hdf format to raster
  VIIRS_day.py: nighttime lights data pre-processing
  VIIRS-month_EULUC.py: monthly composite nighttime lights images and Land use data(EULUC) pre-processing
  trend.py: calculate the trend of each pixel in nighttime lights images
  Mosaic.py: raster mosaic
  resume_rate.py：calculate work resumption index based on nighttime lights data
