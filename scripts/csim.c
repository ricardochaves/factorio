// Fluid belt simulation core. Arrays describe splitters (in/out edge ids, -1 if none) and merges.
#include <math.h>
#include <stdlib.h>
static inline double dmin(double a,double b){return a<b?a:b;}
static inline double dmax(double a,double b){return a>b?a:b;}
int run(int ne,const double*cap,int ns,const int*sin_,const int*sout,const int*iprio,const int*oprio,
        int nm,const int*mstart,const int*mins,const int*mout,
        double*s,double*d,double tol,int max_iter){
  int it=0;
  while(it<max_iter){
    it++; double delta=0;
    for(int k=0;k<ns;k++){
      int ia=sin_[2*k],ib=sin_[2*k+1],oc=sout[2*k],od=sout[2*k+1];
      double sa=ia>=0?s[ia]:0,sb=ib>=0?s[ib]:0,dc=oc>=0?d[oc]:0,dd=od>=0?d[od]:0;
      double I=sa+sb,O=dc+dd,nsc,nsd,nda,ndb;
      if(oprio[k]==0){nsc=I;nsd=I-dmin(I,dc);} else if(oprio[k]==1){nsd=I;nsc=I-dmin(I,dd);} else {nsc=dmax(I/2,I-dd);nsd=dmax(I/2,I-dc);}
      if(iprio[k]==0){nda=O;ndb=O-dmin(O,sa);} else if(iprio[k]==1){ndb=O;nda=O-dmin(O,sb);} else {nda=dmax(O/2,O-sb);ndb=dmax(O/2,O-sa);}
      double v;
      if(oc>=0){v=dmin(cap[oc],nsc);delta=dmax(delta,fabs(v-s[oc]));s[oc]=v;}
      if(od>=0){v=dmin(cap[od],nsd);delta=dmax(delta,fabs(v-s[od]));s[od]=v;}
      if(ia>=0){v=dmin(cap[ia],nda);delta=dmax(delta,fabs(v-d[ia]));d[ia]=v;}
      if(ib>=0){v=dmin(cap[ib],ndb);delta=dmax(delta,fabs(v-d[ib]));d[ib]=v;}
    }
    for(int k=0;k<nm;k++){
      int o=mout[k]; if(o<0) continue;
      int a=mstart[k],b=mstart[k+1],n=b-a; double I=0;
      for(int j=a;j<b;j++) I+=s[mins[j]];
      double v=dmin(cap[o],I);delta=dmax(delta,fabs(v-s[o]));s[o]=v;
      double O=d[o];
      for(int j=a;j<b;j++){int i=mins[j];double others=I-s[i];v=dmin(cap[i],dmax(O/n,O-others));delta=dmax(delta,fabs(v-d[i]));d[i]=v;}
    }
    if(delta<tol) break;
  }
  return it;
}
