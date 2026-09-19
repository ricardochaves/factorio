// Time-stepped "bucket" belt simulation: every edge is a buffer of items, splitters move items each tick.
// Starts from whatever state q[] holds (empty belts = zeros) so that history matters like in the real game.
#include <math.h>
#include <stdlib.h>
#include <string.h>
static inline double dmin(double a,double b){return a<b?a:b;}
static inline double dmax(double a,double b){return a>b?a:b;}
// split total F between two ports with limits l0,l1 (l0+l1>=F). prio: -1 none, 0/1 preferred port.
static inline void share(double F,double l0,double l1,int prio,double*o0,double*o1){
  if(prio==0){*o0=dmin(l0,F);*o1=F-*o0;}
  else if(prio==1){*o1=dmin(l1,F);*o0=F-*o1;}
  else{double h=F/2; if(l0<h){*o0=l0;*o1=F-l0;} else if(l1<h){*o1=l1;*o0=F-l1;} else{*o0=h;*o1=h;}}
}
void run_dyn(int ne,const double*cap,const double*rf,int ns,const int*sin_,const int*sout,const int*iprio,const int*oprio,
             int nsrc,const int*src_e,const double*supply,int nsnk,const int*snk_e,const double*demand,
             double*q,int ticks,double rate,double*acc_in,double*acc_out){
  double*din=(double*)calloc(ne,sizeof(double));   // added to edge this tick
  double*dout=(double*)calloc(ne,sizeof(double));  // removed from edge this tick
  for(int i=0;i<nsrc;i++)acc_in[i]=0; for(int j=0;j<nsnk;j++)acc_out[j]=0;
  for(int t=0;t<ticks;t++){
    memset(din,0,ne*sizeof(double)); memset(dout,0,ne*sizeof(double));
    for(int i=0;i<nsrc;i++){int e=src_e[i]; if(e<0)continue; double v=dmin(rate*supply[i]*rf[e],cap[e]-q[e]); if(v<0)v=0; din[e]+=v; acc_in[i]+=v;}
    for(int j=0;j<nsnk;j++){int e=snk_e[j]; if(e<0)continue; double v=dmin(rate*demand[j]*rf[e],q[e]); dout[e]+=v; acc_out[j]+=v;}
    for(int k=0;k<ns;k++){
      int ia=sin_[2*k],ib=sin_[2*k+1],oc=sout[2*k],od=sout[2*k+1];
      double a0=ia>=0?dmin(rate*rf[ia],q[ia]):0,a1=ib>=0?dmin(rate*rf[ib],q[ib]):0;
      double b0=oc>=0?dmax(0,dmin(rate*rf[oc],cap[oc]-q[oc])):0,b1=od>=0?dmax(0,dmin(rate*rf[od],cap[od]-q[od])):0;
      double F=dmin(a0+a1,b0+b1); if(F<=0)continue;
      double x0,x1,y0,y1;
      share(F,a0,a1,iprio[k],&x0,&x1); share(F,b0,b1,oprio[k],&y0,&y1);
      if(ia>=0)dout[ia]+=x0; if(ib>=0)dout[ib]+=x1; if(oc>=0)din[oc]+=y0; if(od>=0)din[od]+=y1;
    }
    for(int e=0;e<ne;e++){q[e]+=din[e]-dout[e]; if(q[e]<0)q[e]=0; if(q[e]>cap[e])q[e]=cap[e];}
  }
  free(din);free(dout);
}
