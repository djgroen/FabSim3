import numpy as np

def smooth_data(x,window_len=13,window='flat'):
  """smooth the data using a window with requested size. courtesy of the scipy cookbook.
  This method is based on the convolution of a scaled window with the signal.
  The signal is prepared by introducing reflected copies of the signal 
  (with the window size) in both ends so that transient parts are minimized
  in the begining and end part of the output signal. Output length equals input length here
  """
  if x.ndim != 1:
    raise ValueError, "smooth only accepts 1 dimension arrays."
  if x.size < window_len:
    raise ValueError, "Input vector needs to be bigger than window size."
  if window_len<3:
    return x   
  if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
    raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"   
  s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
  if window == 'flat': #moving average
    w=np.ones(window_len,'d')
  else:
    w=eval('np.'+window+'(window_len)')      
  y=np.convolve(w/w.sum(),s,mode='valid')
    
  return y[(window_len/2):-(window_len/2)]
  

def remove_tail(pot, der, window_len=13, window='flat'):
  """removes the tail outside of 0 in a data set """
  stop = 0
  iter_count = 0
  while stop==0:
    iter_count += 1
    if(np.abs(pot[-iter_count]) < 0.001):
      stop = 1

  for i in xrange(0,iter_count):
	j = iter_count - i
	pot[-j] = 0.0
	der[-j] = -pot[-(j+1)]
  
  return pot, der 

  
def append_zeroes(dis, pot, der, new_threshold):
  """ Append zeroes to the potential to the new cutoff
  """
  increment = dis[2] - dis[1]

  while dis[-1] < new_threshold:
	dis = np.append(dis,[dis[-1]+increment])
	pot = np.append(pot,[0.0])
	der = np.append(der,[0.0])
	
  return dis, pot, der

def append_linear(dis, pot, der, new_threshold):
  """ Append linear values to the potential to the new cutoff
  """
  increment = dis[2] - dis[1]

  while dis[-1] < new_threshold:
    dis = np.append(dis,[dis[-1]+increment])
    pot = np.append(pot, 2*pot[-1] + pot[-2])
    der = np.append(der, der[-1])

  return dis, pot, der

def prepend_linear(dis, pot, der, new_threshold):
  """ Append linear values to the potential to the new cutoff
  """
  increment = dis[2] - dis[1]
  print dis[0], new_threshold

  while new_threshold < dis[0]:
    dis = np.insert(dis, 0, dis[0]-increment)
    pot = np.append(pot, 0, 2*pot[0] - pot[1])
    der = np.append(der, 0, der[0])
    print "iteration:", dis[0], pot[0], der[0]

  return dis, pot, der

