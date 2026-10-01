#include <math.h>
#ifdef __cplusplus
#define LINKAGE extern "C"
#else
#define LINKAGE
#endif
#ifdef _WIN32
#define API LINKAGE __declspec(dllexport)
#else
#define API LINKAGE
#endif
#ifdef _WIN32
int __stdcall DllMain(void* module,unsigned long reason,void* reserved){return 1;}
static double (*core_cos)(double);
static double (*core_sin)(double);
static double (*core_tanh)(double);
API void set_math(double (*cos_fn)(double),double (*sin_fn)(double),double (*tanh_fn)(double)){
    core_cos=cos_fn;core_sin=sin_fn;core_tanh=tanh_fn;
}
#else
#define core_cos cos
#define core_sin sin
#define core_tanh tanh
#endif
static double clamp(double x,double a,double b){return x<a?a:x>b?b:x;}

// Body-frame error: reference minus estimated pose. Gains include LQR design.
API void trajectory_control(int nonlinear,double ex,double ey,double ep,
                            double vr,double wr,const double* gains,double* out){
    if(nonlinear){
        out[0]=vr*core_cos(ep)+gains[0]*ex;
        out[1]=wr+gains[1]*vr*ey+gains[2]*core_sin(ep);
    }else{
        out[0]=vr+gains[0]*ex;
        out[1]=wr+gains[1]*ey+gains[2]*ep;
    }
}
API double wheel_pi(double target,double measured,double dt,double limit,double* integral){
    const double error=target-measured, kp=0.22, ki=1.0;
    const double trial=*integral+dt*error;
    const double u=kp*error+ki*trial;
    if((u<0?-u:u)<=limit || error*u<0) *integral=trial;
    return clamp(kp*error+ki*(*integral),-limit,limit);
}

// States: x,y,yaw,v,yaw_rate,wl,wr,il,ir. Torque-driven, independent body/wheel speeds.
API void plant_step(double* s,double duty_l,double duty_r,double mu_l,double mu_r,
                    double payload,double dt,int enabled){
    const double r=.075,b=.38,m=12+payload,J=.006, Iz=.55+payload*.04;
    const double N=.85*m*9.81/2, C=500, R=1.5,L=.003,kt=.12,ke=.12;
    const double gl=s[3]-b*s[4]/2,gr=s[3]+b*s[4]/2;
    const double fl=mu_l*N*core_tanh(clamp(C*(r*s[5]-gl)/(mu_l*N),-15.,15.));
    const double fr=mu_r*N*core_tanh(clamp(C*(r*s[6]-gr)/(mu_r*N),-15.,15.));
    const double il_dot=enabled?(24*duty_l-R*s[7]-ke*s[5])/L:-R*s[7]/L;
    const double ir_dot=enabled?(24*duty_r-R*s[8]-ke*s[6])/L:-R*s[8]/L;
    const double vdot=(fl+fr-1.4*core_tanh(s[3]/.05)-.35*s[3])/m;
    const double wdot=((fr-fl)*b/2-.08*s[4])/Iz;
    const double wldot=(kt*s[7]-r*fl-.003*s[5])/J;
    const double wrdot=(kt*s[8]-r*fr-.003*s[6])/J;
    s[0]+=dt*s[3]*core_cos(s[2]);s[1]+=dt*s[3]*core_sin(s[2]);s[2]+=dt*s[4];
    s[3]+=dt*vdot;s[4]+=dt*wdot;s[5]+=dt*wldot;s[6]+=dt*wrdot;
    s[7]+=dt*il_dot;s[8]+=dt*ir_dot;
}

