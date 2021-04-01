#!/user/bin/env python
# -*- coding:utf-8 -*-
import os
import rw_tif
import numpy as np
from osgeo import gdal



def times(reflect_d):
    light_db=0
    light_de=0
    if reflect_d<=31:
        light_db=100+reflect_d
        light_de=light_db+7
        if light_de>131:
            light_de =200+light_de-131
    elif reflect_d<=31+29:
        light_db=200+reflect_d-31
        light_de = light_db + 7
        if light_de > 229:
            light_de = 300 + light_de - 229
    elif reflect_d<=31+29+31:
        light_db = 300 + reflect_d - (31+29)
        light_de = light_db + 7
        if light_de > 331:
            light_de = 400 + light_de - 331
    elif reflect_d<=31+29+31+30:
        light_db = 400 + reflect_d - (31+29+31)
        light_de = light_db + 7
        if light_de > 430:
            light_de = 500 + light_de - 430
    elif reflect_d<=31+29+31+30+31:
        light_db = 500 + reflect_d - (31 + 29 + 31+30)
        light_de = light_db + 7
        if light_de > 531:
            light_de = 600 + light_de - 531
    return light_db,light_de


def get_index(day,time):
    m=0
    if day[5]=='2':
        m+=31
    elif day[5]=='3':
        m=31+29
    elif day[5]=='4':
        m=31+29+31
    elif day[5]=='5':
        m = 31 + 29 + 31+30
    index=1440*(m+int(day[6:8])-1)+int(time[:2])*60+int(time[2:])
    return index

#Get Em
def get_Em(day,time):
    E_file = r'H:\research\light\code\outext.txt'   #TOA lunar spectral irradiance obtained from the MT2009 model
    f = open(E_file, "r")  # "r" 可写可不写
    content = f.readlines()
    f.close()
    newday,_=times(day)
    newtime=time.astype(int)*100+((time-time.astype(int))*60).astype(int)
    Em=np.zeros(time.shape)
    del time
    timeindex=np.unique(newtime)
    for i in timeindex:
        if i>0:
            r=np.where(newtime==i)
            index = get_index('20200'+str(newday), str(i))
            Em[r]=float(content[index][28:51])
    del newtime,timeindex,content
    return Em

#VNP46A1 pre-processing
def VNP46_process(light_t,angle_t,cloud_t,reflect_t,time_t,day,filename):
    ldata, im_proj, im_geotrans, _, _,_ = rw_tif.read(light_t)
    ldata = ldata * 0.1
    if os.path.exists(reflect_t):
        tdata=rw_tif.get_data(time_t)

        Em=get_Em(day, tdata)
        del tdata
        Lm=np.zeros(ldata.shape)
        adata = rw_tif.get_data(angle_t)
        rdata = rw_tif.get_data(reflect_t)
        r = np.where((ldata > 0) & (rdata > 0))
        Lm[r]=Em[r]*100*(rdata[r]/10000)*np.cos(adata[r]*0.01*np.pi/180)/np.pi
        r=np.where(Lm>0)
        ldata[r]-=Lm[r]
        r=np.where(ldata<0)
        ldata[r]=0
        del Em,Lm,adata,rdata
    cdata = rw_tif.get_data(cloud_t)
    r=np.where(~((cdata&1==0)&((cdata>>1 & 7==0)|(cdata>>1 & 7==1)|(cdata>>1 & 7==5))&(cdata>>5&1==1)&(cdata>>7&15==0)))
    ldata[r] = -1000
    del cdata
    rw_tif.write(filename,im_proj,im_geotrans,ldata,-1000)
    del ldata
def VNP46(inpath,angle,cloud,reflect,time,out):
    f=os.listdir(inpath)
    for i in range(len(f)):
        light_t=inpath+'\\'+f[i]
        angle_t=angle+'\\'+f[i]
        cloud_t=cloud+'\\'+f[i]
        reflect_t=reflect+'\\'+f[i]
        time_t=time+'\\'+f[i]
        outfile= out + '\\' + f[i]
        day=int(f[i][13:16])
        VNP46_process(light_t, angle_t, cloud_t, reflect_t, time_t, day,outfile)


#VNP46 image outlier removal
def remove_outlier(inpath,outpath,monthpath):
    f = os.listdir(inpath)

    for i in range(len(f)):
        if f[i].endswith('.tif'):
            if f[i][17:20]=='061':
                outpath[-4:]='2003'
            imdata,im_proj,im_geotrans,_,_=rw_tif.read(inpath+'\\'+f[i])

            data_month=rw_tif.get_data(os.path.join(monthpath,f[i][17:23]+'.tif'))

            r=np.where((imdata-data_month>0.5*data_month)&(imdata-data_month>10))
            imdata[r]=-1000
            r=np.where((imdata<0.5*data_month)&(data_month-imdata>10))
            imdata[r] = -1000

            outfile = outpath + '\\' + f[i][13:23]+'.tif'
            rw_tif.write(outfile, im_proj, im_geotrans, imdata,nodata=-1000)
            del imdata,data_month

#Image Splicing
def joint(inpath,outpath):
    f = os.listdir(inpath)
    files = []
    day=f[0][:3]
    for i in f:
        if i[:3]==day :
            files.append(os.path.join(inpath, i))
        else:
            gdal.Warp(os.path.join(outpath, day+'.tif'), files, srcNodata=-1000)
            if i[:3]=='090':
                break
            files=[]
            files.append(os.path.join(inpath, i))
            day=i[:3]
    gdal.Warp(os.path.join(outpath, day + '.tif'), files, srcNodata=-1000)


if __name__=='__main__':
    os.chdir(r'F:')

    #VNP46A1 pre-processing
    VNP46('VNP46\\tif\\light','VNP46\\tif\\angle','VNP46\\tif\\cloud','VNP46\\tif\\reflect','VNP46\\tif\\time','VNP46\\tif\\out')

    #VNP46 image outlier removal
    remove_outlier('VNP46\\tif\\out','VNP46\\tif\\out_no_outlier','VNP46\\tif\\2002')

    # Image Splicing
    joint('VNP46\\tif\\out_no_outlier', 'VNP46\\tif\\joint')

