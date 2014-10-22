import numpy as np
from scipy.optimize import leastsq

def derivatives(x, y):
  num_x = len(x);
  deriv = np.zeros((len(x)))
  
  # If there for two input points, use a straight line as the derivative.
  if num_x == 2:
    deriv[0] = (y[1] - y[0]) / (x[1] - x[0])
    deriv[1] = deriv[0]
    return deriv

  # Calculate the derivatives for the interior points. This loop uses
  # a total of 6 points to calculate the derivative at any one
  # point. And when the loop moves along in increasing array
  # position, the same data point is used three times. So instead of
  # reading the correct value from the array three times, just shift
  # the values down by copying them from one variable to the next.
  xi = 2*x[0]-x[1] # 0.0
  xj = x[0]
  xk = x[1]
  yi = 2*y[0]-y[1] # 0.0
  yj = y[0]
  yk = y[1]

  for i in xrange(1, num_x-1): 
    xi = xj
    xj = xk
    xk = x[i+1]
    yi = yj
    yj = yk
    yk = y[i+1]
    r1 = (xk - xj)*(xk - xj) + (yk - yj)*(yk - yj)
    r2 = (xj - xi)*(xj - xi) + (yj - yi)*(yj - yi)
    deriv[i] = ( (yj - yi)*r1 + (yk - yj)*r2 ) / ( (xj - xi)*r1 + (xk - xj)*r2 )

  # Calculate the derivative at the first point, (x(0),y(0)).
  slope = (y[1] - y[0]) / (x[1] - x[0])
  if ((slope >= 0) and (slope >= deriv[1])) or ((slope <= 0) and (slope <= deriv[1])):
    deriv[0] = 2 * slope - deriv[1]
  else:
    deriv[0] = slope + (abs(slope) * (slope - deriv[1])) / (abs(slope) + abs(slope - deriv[1]))

  # Calculate the derivative at the last point.
  slope = (y[num_x-1] - y[num_x-2]) / (x[num_x-1] - x[num_x-2])
  if ((slope >= 0) and (slope >= deriv[num_x-2])) or ((slope <= 0) and (slope <= deriv[num_x-2])):
    deriv[num_x-1] = 2 * slope - deriv[num_x-2]
  else:
    deriv[num_x-1] = slope + (abs(slope) * (slope - deriv[num_x-2])) / (abs(slope) + abs(slope - deriv[num_x-2]) )

  return deriv 


def get_centre_of_mass(molecule_particles, bounds):
# calculate centre of mass of a sheet in a periodic box. 
# Becomes incorrect if any structure extends beyond 0.5 of the box size.
  cm_rel = np.array(([0.0, 0.0, 0.0 ]))
  rp = molecule_particles[0] #reference particle
  
  for p in molecule_particles:
    
    for i in xrange(0,3):
      a = p[i] - rp[i]
      if a > 0.5 * bounds[i]:
        a = p[i] - rp[i] - bounds[i]
      elif a < -0.5 * bounds[i]:
        a = p[i] - rp[i] + bounds[i]
      cm_rel[i] += a
  
  cm_rel = cm_rel / len(molecule_particles)  
  cm = rp + cm_rel
  
  cm[0] = cm[0] %bounds[0]
  cm[1] = cm[1] %bounds[1]
  cm[2] = cm[2] %bounds[2]
  
  #print cm
  #import sys
  #sys.exit()
  
  return cm
    

def f_min(X,p):
    plane_xyz = p[0:3]
    distance = (plane_xyz*X.T).sum(axis=1) + p[3]
    return distance / np.linalg.norm(plane_xyz)  

def residuals(params, signal, X):
    return f_min(X, params)
    
def get_fitting_plane(points):
# returns a,b,c,d in ax+by+cz+d=0. a,b,c are also the normal.

  pointsT = points.transpose()
  # Inital guess of the plane
  diff = points[0] - points[-1]
  
  p0 = np.array(([diff[0], diff[1], diff[2], 1.]))

  sol = leastsq(residuals, p0, args=(None, pointsT))[0]

  #print "Solution: ", sol
  #print "Old Error: ", (f_min(pointsT, p0)**2).sum()
  #print "New Error: ", (f_min(pointsT, sol)**2).sum()
  
  return sol
  
  
def unit_vector(vector):
  """ Returns the unit vector of the vector.  """
  return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
# Returns the angle in radians between vectors 'v1' and 'v2' in radians.
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    angle = np.arccos(np.dot(v1_u, v2_u))
    if np.isnan(angle):
        if (v1_u == v2_u).all():
            return 0.0
        else:
            return np.pi
    return angle  