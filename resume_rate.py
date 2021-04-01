#!/user/bin/env python
# -*- coding:utf-8 -*-
import rw_tif
import os
import numpy as np


#fill gaps
def fill_trend(inpath,outpath):
    os.chdir(inpath)
    f = os.listdir(inpath)
    light = rw_tif.get_data(r'F:\EULUC\city_noresident.tif')
    trend=rw_tif.get_data(r'H:\research\light\data\VNP46\tif\trend\trend_clip.tif')
    b=rw_tif.get_data(r'H:\research\light\data\VNP46\tif\trend\b_clip.tif')
    j=0
    for i in range(len(f)):
        if f[i].endswith('.tif'):
            im_datas, im_proj, im_geotrans, _, _,nodata = rw_tif.read(f[i])
            r=np.where((light<1000000)&(trend>-1000)&(im_datas<-999))
            im_datas[r]=trend[r]*(7*j+3)+b[r]
            outfile=os.path.join(outpath,f[i])
            rw_tif.write(outfile, im_proj, im_geotrans, im_datas,nodata)
            del im_datas, r
            j+=1


#Calculate the work resumption index
def WRI(path,regionfile):
    f_light=os.listdir(path)
    regiondata=rw_tif.get_data(regionfile)

    min=rw_tif.get_data(r'F:\VNP46\tif\week_fill\min.tif')  #Average lighting images during the Chinese New Year holiday
    max=rw_tif.get_data(r'F:\VNP46\tif\month\201903_noresident.tif')  #Monthly average composite images for March 2019
    increase=rw_tif.get_data(r'F:\VNP46\tif\month\increase.tif')   #Images of growth in nighttime lighting from 2018 to 2019
    f = open(r"F:\VNP46\tif\out.txt", "w")   # 打开文件以便写入
    
    for i in range(len(f_light)):
        if f_light[i].endswith('.tif') :
            data=rw_tif.get_data(os.path.join(path,f_light[i]))

            l = [110100,440100]  #City Number; For example, Beijing: 110100
            for j in l:
                r=np.where((regiondata==j)&(data>0)&(min>0)&(max>0))
                num2=np.sum((regiondata==j)&(max>0))
                if len(r[0])>num2*0.5:
                    rate=1 - (np.sum(max[r])+np.sum(increase[r]) - np.sum(data[r])) / (np.sum(max[r])+np.sum(increase[r]) - np.sum(min[r]))
                    print(j,len(r[0]),np.sum(min[r]),np.sum(data[r]),np.sum(max[r]),np.sum(increase[r]),rate,file=f)
                else:
                    print(j,np.sum(data[r]),file=f)
            del data
    f.close()

    del regiondata,min,max


if __name__=='__main__':
    #fill gaps
    fill_trend(r'F:\VNP46\tif\week',r'F:\VNP46\tif\week_fill')

    #Calculate the work resumption index
    WRI(r'F:\VNP46\tif\week_fill',r'F:\EULUC\city_noresident.tif')
