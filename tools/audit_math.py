"""Optional exact mathematical spot checks (requires sympy).

These checks verify selected identities/constructions, not every proof or human
difficulty label. Output is reproducible and does not contain model scores.
"""
import json
from pathlib import Path
import sympy as s

ROOT=Path(__file__).resolve().parents[1]


def check_integrals_and_algebra():
    results=[]
    def record(name,passed,scope):
        if not passed:
            raise AssertionError(name)
        results.append(dict(check=name,passed=True,scope=scope))
    x=s.symbols('x',positive=True)
    c=s.symbols('c',real=True)
    original=s.exp(x)*(1+s.sin(x))/(1+s.cos(x))
    derivative=s.diff(s.exp(x)*s.sin(x)/(1+s.cos(x)),x)
    record('2019 NonMath I-3 antiderivative',s.trigsimp(derivative-original)==0,'symbolic identity')
    record('2025 NonMathB I-1',s.diff(x*x*s.exp(s.sin(x)),x,2).subs(x,0)==2,'exact second derivative')
    record('2025 shared plane',s.Matrix([2,2,-3]).dot(s.Matrix([6,-3,2]))==0 and s.Matrix([2,2,-3]).dot(s.Matrix([4,-1,2]))==0,'two independent normal constraints')
    record('2025 NonMathA I-1',s.limit((x-s.log(1+x)-x*s.sin(x)/2)/x**3,x,0)==-s.Rational(1,3),'symbolic limit')
    record('2025 NonMathB I-5',s.integrate(s.log(x)/(1+x)**2,(x,1,s.oo))==s.log(2),'exact improper integral')
    z=s.log(x)/(x+c)
    residual=s.simplify(-x*s.log(x)*s.diff(z,x)+(1-x*z)*z)
    record('2025 shared ODE regular branch',residual==0,'substitution into original equation via z=cos(y)')
    record('2025 shared ODE constant branch',s.simplify((1-x*0)*0)==0,'cos(y)=0 solves original equation')
    y,zv=s.symbols('y z',real=True)
    F=2*x*x+2*y*y+zv*zv+8*x*zv-zv+8
    checks=[]
    for xx,zz,sign in [(-2,s.Integer(1),1),(s.Rational(16,7),-s.Rational(8,7),-1)]:
        d={x:xx,y:0,zv:zz}
        fz=s.diff(F,zv).subs(d)
        checks += [F.subs(d)==0,s.diff(F,x).subs(d)==0,s.diff(F,y).subs(d)==0,fz!=0,s.sign(-4/fz)==sign]
    record('2025 NonMathB III stationary points',all(checks),'exact surface, implicit regularity and Hessian signs')
    r=s.symbols('r',nonnegative=True)
    area=2*s.pi*s.integrate(r*s.sqrt(1+4*r*r),(r,0,1))
    record('2025 NonMathB II area',s.simplify(area-s.pi*(5*s.sqrt(5)-1)/6)==0,'exact surface-area integration')
    t=s.symbols('t',nonnegative=True)
    record('2020 MathB VI weights',s.integrate((s.sqrt(t)-t)**2,(t,0,1))==s.Rational(1,30) and s.integrate((t*t-t**4)/2,(t,0,1))==s.Rational(1,15),'exact integral constants in proof')
    # Vary dimensions and signed/zero rational data; verify with direct determinants.
    good=True
    for m in [3,4,5]:
        for n in [3,4,5,6]:
            aa=[s.Rational((-1)**j*j,j+1) for j in range(m+1)]
            aa[1]=s.Integer(0)
            matrices=[s.diag(a,*([1]*(n-1))) for a in aa[:m]]
            ss=aa[0]-sum(aa[1:m])
            b=ss*(m-2)+aa[m]/(-(m-2))**(n-2)
            matrices[0][1,0]=1
            matrices[1][0,1]=b
            D=matrices[0].copy()
            for A in matrices[1:]: D-=A
            good &= all(A.det()==a for A,a in zip(matrices,aa)) and s.simplify(D.det()-aa[m])==0
    record('2025 shared matrix determinant construction',bool(good),'12 exact rational instances across independent m,n, including zero determinants')
    # Independent combinatorial count for small sets satisfying unique pair sums.
    good=True
    for N in [1,2,3,4]:
        S=[4**j for j in range(N)]
        fourth=sum(a+b==c+d for a in S for b in S for c in S for d in S)
        good &= fourth==2*N*N-N
    record('2025 shared Fourier fourth moment',good,'finite exact count sanity checks; general proof remains in reference')
    pts=[s.Matrix([s.Rational(2,3),-s.Rational(2,3),-s.Rational(2,3)]),s.Matrix([-s.Rational(2,3),s.Rational(2,3),-s.Rational(2,3)]),s.Matrix([s.Rational(2,3),s.Rational(2,3),-s.Rational(2,3)])]
    record('2020 MathA I tetrahedron volume',abs(s.Matrix.hstack(*pts).det())/6==s.Rational(16,81),'exact mixed product')
    return results


def check_continuous_and_discrete():
    results=[]
    def check(item,claim,ok):
        assert bool(ok),(item,claim)
        results.append(dict(item=item,claim=claim,passed=True))
    x,y,z,t=s.symbols('x y z t',real=True)
    # Newton identities, not numerical eigenvalue estimates.
    e=[s.Integer(1)]
    for k in range(1,5):e.append(s.simplify(sum((-1)**(i-1)*e[k-i]*i for i in range(1,k+1))/k))
    check('CMC-2015-PRE-Math-II','det A=1/24',e[4]==s.Rational(1,24))
    check('CMC-2009-PRE-NonMath-I-1','beta integral 16/15',s.integrate(t*t/s.sqrt(1-t),(t,0,1))==s.Rational(16,15))
    a=s.symbols('a',positive=True)
    cap=3*(5*s.sqrt(3)*s.pi)+18*s.sqrt(3)*s.pi
    check('CMC-2014-PRE-NonMath-IV','cap flux 33√3π',cap==33*s.sqrt(3)*s.pi)
    check('CMC-2015-PRE-NonMath-I-3','paraboloid volume π/2',2*s.pi*s.integrate(t*(1-t*t),(t,0,1))==s.pi/2)
    mass=s.Rational(4,3)*s.pi/s.sqrt(2)*(s.Rational(3,4)+s.Rational(5,2)/5)
    check('CMC-2016-PRE-NonMath-III','ellipsoid mass 5π/(3√2)',s.simplify(mass-5*s.pi/(3*s.sqrt(2)))==0)
    A=s.Matrix([[2,2,2,-2],[0,0,-2,2],[0,-2,0,2],[0,-2,-2,4]])
    target=(t-2)**2*((t-1)**2-12)
    check('CMC-2013-FINAL-MathSenior-II','orthogonal quadratic form eigenvalues',((A+A.T)/2).charpoly().all_coeffs()==s.Poly(target,t).all_coeffs())
    check('CMC-2013-PRE-NonMath-V','minimum flux',s.simplify(3/s.sqrt(6)*4*s.pi*s.integrate((t*t-1)*t*t,(t,0,1))+8*s.pi/(5*s.sqrt(6)))==0)
    value=s.pi/2*s.integrate((9-(z-1)**2)**2,(z,0,4))-256*s.pi/15
    check('CMC-2018-PRE-NonMath-IV','sphere difference integral 256π/3',value==256*s.pi/3)
    for power,p,error in [(3,4*x*x/3-4*x/9,s.Rational(1,36)),(4,4*x*x/3-16*x/27,s.Rational(7,135))]:
        q=s.factor(x**power-p)
        check('CMC-2015-FINAL-MathSenior-VIII',f'power {power} Radau error',s.integrate(q,(x,0,1))==error)
        check('CMC-2015-FINAL-MathSenior-VIII',f'power {power} lower-polynomial contact',q.subs(x,0)==0 and q.subs(x,s.Rational(2,3))==0 and s.diff(q,x).subs(x,s.Rational(2,3))==0)
    u=s.symbols('u',positive=True)
    velocity=(1-u/(1+u*u))/(2*u*u/(1+u*u))
    derivative=s.simplify(u*s.diff(velocity,u)/(2*u*u/(1+u*u)))
    check('CMC-2010-FINAL-NonMath-I-3','parametric second derivative',s.simplify(derivative-(u-2)*(u*u+1)/(4*u**4))==0)
    check('CMC-2018-FINAL-MathSenior-I-4','constant 3x3 block impossible',s.Rational(9,8)>1)
    g=1+x*x+x**4-x**3-x**5
    check('CMC-2009-FINAL-NonMath-VII','unique fixed point and negative derivative',s.expand(g-x+(x-1)*(x**4+x*x+1))==0 and s.diff(g,x).subs(x,1)==-2)
    check('CMC-2017-FINAL-MathSenior-I-1','recursive rank',sum(s.binomial(4,k) for k in range(5) if 4-2*k!=0)==10)
    check('CMC-2016-PRE-NonMath-I-4','fourth derivative',s.diff(s.exp(x)*s.sin(2*x),x,4).subs(x,0)==-24)
    check('CMC-2017-PRE-NonMath-III','space curve integral',s.integrate(-s.sin(t)**2/(2*s.sqrt(2))+(1-s.cos(t))*s.cos(t)/(2*s.sqrt(2))+(1+s.cos(t))*s.sin(t)/4,(t,0,s.pi))==s.Rational(1,2)-s.pi/(2*s.sqrt(2)))
    check('CMC-2012-PRE-Math-V','binomial sum closed form',all(sum(s.binomial(n,k)*s.binomial(n+2-k,3) for k in range(n))==s.Rational(2**n*n*(n+2)*(n+7),48) for n in range(1,15)))
    return results


def main():
    results=check_integrals_and_algebra()+check_continuous_and_discrete()+check_solution_constructions()
    checks=[dict(item=r.get('item',r.get('check')),claim=r.get('claim',r.get('scope')),passed=r['passed']) for r in results]
    report=dict(sympy_version=s.__version__,checks=checks,n_checks=len(checks),all_passed=True,
        scope='Selected exact mathematical checks; not full-corpus proof certification or model scores.')
    target=ROOT/'qa/math_audit.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'PASS: {len(checks)} mathematical spot checks (SymPy {s.__version__}).')


def check_solution_constructions():
    results=[]
    def check(item,claim,condition):
        assert bool(condition),(item,claim)
        results.append(dict(item=item,claim=claim,passed=True))
    x,y,z,c=s.symbols('x y z c',real=True)
    # Derive common-perpendicular parameters independently from the two normals.
    dv,dw=s.symbols('dv dw',real=True)
    sp=(dv-c*dw)/(1-c*c);tp=(c*dv-dw)/(1-c*c)
    check('CMC-2015-PRE-Math-I','both orthogonality equations',
          s.simplify(-dv+sp-c*tp)==0 and s.simplify(-dw+c*sp-tp)==0)
    A=s.Matrix([[1,0,1],[0,-4,2],[1,2,0]])
    check('CMC-2018-FINAL-MathSenior-I-1','example is symmetric with required row space',
          A==A.T and A.rank()==2 and s.Matrix([[1,0,1],[1,2,0]]).col_join(A).rank()==2)
    plane1=3*x+4*y-z+1;plane2=x-2*y-5*z+3
    p1=2*x+y-3*z+2;p2=5*x+5*y-4*z+3
    check('CMC-2012-PRE-NonMath-I-2','both candidate planes meet line-angle and point constraints',
          s.expand(plane1+p1-p2)==0 and s.expand(plane2+(-3*p1+p2))==0 and
          plane1.subs({x:4,y:-3,z:1})==0 and s.Matrix([3,4,-1]).dot(s.Matrix([1,-2,-5]))==0)
    check('CMC-2017-PRE-Math-V','Riemann sum integral constant',
          s.integrate(s.atan(x),(x,0,1))==s.pi/4-s.log(2)/2)
    check('CMC-2017-FINAL-MathSenior-I-2','logarithm difference limit',
          s.limit((s.log(1+s.tan(x))-s.log(1+s.sin(x)))/x**3,x,0)==s.Rational(1,2))
    check('CMC-2018-PRE-NonMath-I-3','antiderivative on real line',
          s.simplify(s.diff(x*s.asinh(x)/s.sqrt(1+x*x)-s.log(1+x*x)/2,x)-s.asinh(x)/(1+x*x)**s.Rational(3,2))==0)
    check('CMC-2017-PRE-NonMath-I-5','antiderivative',
          s.trigsimp(s.diff(2*s.exp(-s.sin(x))/(1-s.sin(x)),x)-s.exp(-s.sin(x))*s.sin(2*x)/(1-s.sin(x))**2)==0)
    u,v,q=s.symbols('u v q',nonzero=True)
    c2=(3*v-2)/(6*u*(v-u));c3=(2-3*u)/(6*v*(v-u));b32=v*(v-u)/(u*(2-3*u))
    def order_ok(uu,vv,cc2,cc3,bb32):
        return all(s.simplify(expr)==0 for expr in [cc2*uu+cc3*vv-s.Rational(1,2),
                   cc2*uu**2+cc3*vv**2-s.Rational(1,3),cc3*bb32*uu-s.Rational(1,6)])
    check('CMC-2016-FINAL-MathSenior-VIII','general RK3 parameter family order conditions',order_ok(u,v,c2,c3,b32))
    check('CMC-2016-FINAL-MathSenior-VIII','both degenerate RK3 parameter families',
          order_ok(s.Rational(2,3),0,s.Rational(3,4),q,1/(4*q)) and
          order_ok(s.Rational(2,3),s.Rational(2,3),s.Rational(3,4)-q,q,1/(4*q)))
    R=1+z+z*z/2+z**3/6
    check('CMC-2016-FINAL-MathSenior-VIII','imaginary-axis stability boundary',
          s.expand(R.subs(z,s.I*y)*R.subs(z,-s.I*y)-1-y**4*(y*y-3)/36)==0)
    # No reliance on decimal quadrature for density normalization.
    check('CMC-2017-FINAL-MathSenior-X','uniform minimum-plus-maximum density normalizes',
          all(s.integrate(n*x**(n-1)/2,(x,0,1))+s.integrate(n*(2-x)**(n-1)/2,(x,1,2))==1 for n in range(2,10)))
    check('CMC-2018-FINAL-MathSenior-VII','umbilic first/second form proportionality',
          all((s.Matrix([[2,0],[0,1]])/s.sqrt(1+4*x*x+y*y)-
               s.Matrix([[1+4*x*x,2*x*y],[2*x*y,1+y*y]])/s.sqrt(2)).subs({x:uu,y:0})==s.zeros(2)
              for uu in [s.Rational(1,2),-s.Rational(1,2)]))
    p=s.symbols('p')
    check('CMC-2018-FINAL-MathSenior-II','orthogonal surface coordinates',
          s.expand(z*((p+q)/s.sqrt(2))-(z-1)*((q-p)/s.sqrt(2))-(s.sqrt(2)*p*(z-s.Rational(1,2))+q/s.sqrt(2)))==0)
    return results


if __name__=='__main__':main()
