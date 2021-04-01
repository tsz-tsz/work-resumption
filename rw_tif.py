#!/user/bin/env python
# -*- coding:utf-8 -*-
from osgeo import gdal
import numpy as np
import os

def get_data(filename):
    dataset = gdal.Open(filename)
    band = dataset.GetRasterBand(1)
    im_width = dataset.RasterXSize
    im_height = dataset.RasterYSize
    im_datas = band.ReadAsArray(0, 0, im_width, im_height)
    del dataset
    return im_datas


def read(filename):
    #打开文件
    dataset=gdal.Open(filename)
    #栅格矩阵的列数
    im_width = dataset.RasterXSize
    #栅格矩阵的行数
    im_height = dataset.RasterYSize
    #波段数
    im_bands = dataset.RasterCount
    #仿射矩阵，左上角像素的大地坐标和像素分辨率。
    #共有六个参数，分表代表左上角x坐标；东西方向上图像的分辨率；如果北边朝上，地图的旋转角度，0表示图像的行与x轴平行；左上角y坐标；
    #如果北边朝上，地图的旋转角度，0表示图像的列与y轴平行；南北方向上地图的分辨率。
    im_geotrans = dataset.GetGeoTransform()
    #地图投影信息
    im_proj = dataset.GetProjection()
    #读取某一像素点的值
    band = dataset.GetRasterBand(1)
    im_datas = band.ReadAsArray(0,0,im_width,im_height)
    nodata=band.GetNoDataValue()
    del dataset
    return im_datas,im_proj,im_geotrans,im_width,im_height,nodata
    #return im_datas, im_proj, im_geotrans

def write(filename,im_proj,im_geotrans,im_data,nodata=10):
        #gdal数据类型包括
        #gdal.GDT_Byte,
        #gdal .GDT_UInt16, gdal.GDT_Int16, gdal.GDT_UInt32, gdal.GDT_Int32,
        #gdal.GDT_Float32, gdal.GDT_Float64

        #判断栅格数据的数据类型
        if 'int8' in im_data.dtype.name:
            datatype = gdal.GDT_Byte
        elif 'int16' in im_data.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        #判读数组维数
        if len(im_data.shape) == 3:
            im_bands, im_height, im_width = im_data.shape
        else:
            im_bands, (im_height, im_width) = 1,im_data.shape

        #创建文件
        driver = gdal.GetDriverByName("GTiff")            #数据类型必须有，因为要计算需要多大内存空间
        dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)

        dataset.SetGeoTransform(im_geotrans)              #写入仿射变换参数
        dataset.SetProjection(im_proj)                    #写入投影

        if im_bands == 1:
            dataset.GetRasterBand(1).WriteArray(im_data)  #写入数组数据
            if nodata != 10:
                dataset.GetRasterBand(1).SetNoDataValue(nodata)
        else:
            for i in range(im_bands):
                dataset.GetRasterBand(i+1).WriteArray(im_data[i])

        del dataset
