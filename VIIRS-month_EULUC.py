#!/user/bin/env python
# -*- coding:utf-8 -*-
import numpy as np
import rw_tif
import os,gdal

#Larger outliers are removed
def delete_max_value(infile,outfile):
    neighbor=[[-1,-1,-1,0,0,1,1,1],[-1,0,1,-1,1,-1,0,1]]  #The outlier is replaced with an 8-neighborhood
    old,im_proj,im_geotrans,_,height,_=rw_tif.read(infile)
    max=500  #According to the statistics of the Beijing, Shanghai, Guangzhou and Shenzhen, the maximum pixel value does not exceed 500, other regions of the light brightness will not exceed these 4 areas
    r,w=np.where(old>max)
    for i in range(len(r)):
        sum=0
        n=0
        for j in range(8):
            if r[i]+neighbor[0][j]<height and (old[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]<max) and old[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]>-1000:
                sum+=old[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]
                n+=1
        old[r[i]][w[i]]=sum/n
    rw_tif.write(outfile,im_proj,im_geotrans,old)

#Comparison with adjacent time-phase images, eliminating transient light sources
def remove_shortlight(infile,refrefile):
    neighbor = [[-1, -1, -1, 0, 0, 1, 1, 1], [-1, 0, 1, -1, 1, -1, 0, 1]]
    im_datas, im_proj, im_geotrans,_,_,_=rw_tif.read(infile)
    refredata=rw_tif.get_data(refrefile)
    r,w=np.where((im_datas>100)&(im_datas>4*refredata))
    for i in range(len(r)):
        sum=0
        n=0
        flag=False  #是否是处于城市中心
        for j in range(8):
            if r[i]+neighbor[0][j]<0 or r[i]+neighbor[0][j]==im_datas.shape[0] or w[i]+neighbor[1][j]<0 or \
                    w[i]+neighbor[1][j]==im_datas.shape[1]:
                continue
            if refredata[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]>100:
                flag=True
                break
            if (im_datas[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]<100) or \
                    im_datas[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]<=4*refredata[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]:
                sum+=im_datas[r[i]+neighbor[0][j]][w[i]+neighbor[1][j]]
                n+=1
        if flag:
            continue
        im_datas[r[i]][w[i]]=sum/n
    outfile=infile.strip('.tif')+'r.tif'
    rw_tif.write(outfile,im_proj,im_geotrans,im_datas)

#Cropping the image to VNP46A1 image size
def cuttoVNP(infile,outpath,nodata):
    coordinate=[[50,40,50,40,30,50,40,30,50,40,30,20,60,50,40,30,20,60,50,40,30,50],
                [70,70,80,80,80,90,90,90,100,100,100,100,110,110,110,110,110,120,120,120,120,130]]
    name=['h25v04','h25v05','h26v04','h26v05','h26v06','h27v04','h27v05','h27v06','h28v04','h28v05','h28v06','h28v07',
          'h29v03','h29v04','h29v05','h29v06','h29v07','h30v03','h30v04','h30v05','h30v06','h31v04']
    for j in range(len(coordinate[0])):
        outfile = os.path.join(outpath, name[j]+'.tif')
        gdal.Warp(outfile, infile,
                  outputBounds=(coordinate[1][j], coordinate[0][j] - 10, coordinate[1][j] + 10, coordinate[0][j]),
                  srcNodata=nodata)


if __name__=='__main__':
    #Rough cropping of monthly composite nighttime lights images to the Chinese region using arcgis 10.6

    old=r'H:\research\light\data\VIIRS month\202002.tif'
    new=r'H:\research\light\data\VIIRS month\202002_new.tif'
    refre=r'H:\research\light\data\VIIRS month\201912_newr.tif'  #Reference image for outlier removal
    delete_max_value(old,new) #Larger outliers are removed
    remove_shortlight(new,refre) #Comparison with adjacent time-phase images, eliminating transient light sources

    #Based on the VNP46A1 data, the image was resampled to 500m using arcgis10.6

    # Cropping the NTLs monthly composite image to VNP46A1 image size
    cuttoVNP(r'F:\VNP46\tif\month\202002.tif', r'F:\VNP46\tif\2002',-1000)

    #Conversion of EULUC data from shp format to raster, and removal of residential image pixels using arcgis 10.6

    #Cropping the EULUC image to VNP46A1 image size
    cuttoVNP(r'F:\EULUC\noresident.tif', r'F:\VNP46\tif\noresident',-2147483647)