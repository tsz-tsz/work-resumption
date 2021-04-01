#!/usr/bin/python
#-*-coding:utf-8 -*-
# coding=utf-8
import os
import os.path
import gdal
import sys
from gdalconst import *
from osgeo import gdal
import numpy as np

#List file names
def listdatas(inpath,i,name):
    filelist=[]
    files=os.listdir(inpath)
    while files[i][4:10]==name:
        file=os.path.join(inpath,files[i])
        filelist.append(file)
        i = i + 22
        if i>len(files):
            break
    return filelist

#拟合函数
def fit_func(x,a,b):
    return a*x+b
#残差函数
def residuals_func(x,a,b,y):
    ret=fit_func(x,a,b)-y
    return ret


def Read(RasterFile):  # 读取每个图像的信息
    ds = gdal.Open(RasterFile, GA_ReadOnly)
    if ds is None:
        print ('Cannot open ', RasterFile)
        sys.exit(1)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    band = ds.GetRasterBand(1)
    data = band.ReadAsArray(0, 0, cols, rows)
    return data


def Readxy(RasterFile):  # 读取每个图像的坐标信息并返回
    ds = gdal.Open(RasterFile, GA_ReadOnly)
    if ds is None:
        print('Cannot open ', RasterFile)
        sys.exit(1)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    band = ds.GetRasterBand(1)
    # data = band.ReadAsArray(0,0,cols,rows)
    noDataValue = band.GetNoDataValue()
    projection = ds.GetProjection()
    geotransform = ds.GetGeoTransform()
    return rows, cols, geotransform, projection, noDataValue


def WriteGTiffFile(filename, nRows, nCols, data, geotrans, proj, noDataValue, gdalType):  # 向磁盘写入结果文件
    format = "GTiff"
    driver = gdal.GetDriverByName(format)
    ds = driver.Create(filename, nCols, nRows, 1, gdalType)
    ds.SetGeoTransform(geotrans)
    ds.SetProjection(proj)
    ds.GetRasterBand(1).SetNoDataValue(noDataValue)
    ds.GetRasterBand(1).WriteArray(data)
    ds = None

#Calculate the trend of each pixel
def trend(outpath,filelist):
    datalist = []
    rows, cols, geotransform, projection, noDataValue = Readxy(filelist[0])
    for filename in filelist:
        filedata = Read(filename).reshape((1, rows, cols))
        datalist.append(filedata)

    dtaz=[]
    for a in range(len(datalist)):
        if a == 0:
            dtaz = np.concatenate([datalist[a], datalist[a + 1]], axis=0)
        if a > 1:
            dtaz = np.concatenate([dtaz, datalist[a]], axis=0)
    del datalist

    regiondata=Read('F:\\VNP46\\tif\\noresident'+filelist[0].split('\\')[-1][4:10]+'.tif')

    row, col = np.where(regiondata > 0)

    listtime=[]
    for i in range(49):
        listtime.append(i)
    Arraytime = np.array(listtime)

    Time = np.vstack([Arraytime, np.ones(len(Arraytime))]).T #转置
    XL = np.zeros((rows, cols), dtype=np.float)
    Xb = np.zeros((rows, cols), dtype=np.float)
    XL[:] = -1000
    Xb[:] = -1000

    for i in range(len(row)):
        r=row[i]
        c=col[i]
        time=[]
        temparray = []
        for k in range(49):
            if dtaz[k, r, c]!=-1000:
                temparray.append(dtaz[k, r, c])
                time.append(Time[k,:])
        if len(temparray)>=10:
            Arrayslope=np.array(temparray)
            time=np.array(time)

            model,resid=np.linalg.lstsq(time,Arrayslope)[:2]

            XL[r, c] = model[0]
            Xb[r,c]=model[1]

    del dtaz
    trend_out=os.path.join(outpath,'trend_'+filelist[0].split('\\')[-1][4:10]+'.tif')
    WriteGTiffFile(trend_out, rows, cols, XL, geotransform, projection, noDataValue, GDT_Float32)
    b_out=os.path.join(outpath,'b_'+filelist[0].split('\\')[-1][4:10]+'.tif')
    WriteGTiffFile(b_out, rows, cols, Xb, geotransform, projection, noDataValue, GDT_Float32)


if __name__=='__main__':
    name=['h25v04','h25v05','h26v04','h26v05','h26v06','h27v04','h27v05','h27v06','h28v04','h28v05','h28v06','h28v07',
              'h29v03','h29v04','h29v05','h29v06','h29v07','h30v03','h30v04','h30v05','h30v06','h31v04']
    rootdir=r'F:\VNP46\tif\out_no_outlier'
    outdir=r'F:\VNP46\tif\trend'
    for i in range(len(name)):
        filelist = listdatas(rootdir,i,name[i])
        trend(outdir,filelist)       #Calculate the trend of each pixel

    #Image Splicing
    f=os.listdir(outdir)
    b_files=[]
    trend_files=[]
    for i in f:
        if i[:3]=='b_h':
            b_files.append(os.path.join(outdir,i))
        if i[:7]=='trend_h':
            trend_files.append(os.path.join(outdir,i))
    gdal.Warp(os.path.join(outdir,'b.tif'),b_files,srcNodata=-1000)
    gdal.Warp(os.path.join(outdir,'trend.tif'),trend_files,srcNodata=-1000)

    #Cropping of images according to EULUC using arcgis