#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

import sys
import os
import nupic.engine as engine
from PIL import Image

def test_errorHandling():
  n = engine.Network()

  # Test trying to add non-existent node
  try:
    n.addRegion('r', 'py.NonExistingNode', '')
    assert False
  except Exception, e:
    assert str(e) == 'Matching Python module for py.NonExistingNode not found.'

  # Test failure during import
  try:
    n.addRegion('r', 'py.UnimportableNode', '')
    assert False
  except SyntaxError, e:
    assert str(e) == 'invalid syntax (UnimportableNode.py, line 5)'

  # Test failure in the __init__() method
  try:
    n.addRegion('r', 'py.TestNode', '{ failInInit: 1 }')
    assert False
  except Exception, e:
    assert str(e) == 'TestNode.__init__() Failing on purpose as requested'

  # Test failure inside the compute() method
  try:
    r = n.addRegion('r', 'py.TestNode', '{ failInCompute: 1 }')
    r.dimensions = engine.Dimensions([4, 4])
    n.initialize()
    n.run(1)
    assert False
  except AssertionError, e:
    assert str(e) == 'TestNode.compute() Failing on purpose as requested'

  # Test failure in the static getSpec
  from nupic.regions.TestNode import TestNode
  TestNode._failIngetSpec = True
  try:
    TestNode.getSpec()
    assert False
  except AssertionError, e:
    assert str(e) == 'Failing in TestNode.getSpec() as requested'

  del TestNode._failIngetSpec

def test_getSpecFromType():
  ns = engine.Region.getSpecFromType('py.CLARegion')
  p = ns.parameters['breakPdb']
  assert p.accessMode == 'ReadWrite'

def test_one_region_network():
  n = engine.Network()

  print "Number of regions in new network: %d" % len(n.regions)
  assert len(n.regions) == 0

  print "Adding level1SP"
  level1SP = n.addRegion("level1SP", "TestNode", "")
  print "Current dimensions are: %s" % level1SP.dimensions
  print "Number of regions in network: %d" % len(n.regions)

  assert len(n.regions) == 1
  assert len(n.regions) == len(n.regions)

  print 'Node type: ', level1SP.type
  #print 'Nodespec is:'
  #print getSpecString(level1SP.getSpec())

  print "Attempting to initialize net when one region has unspecified dimensions"
  print "Current dimensions are: %s" % level1SP.dimensions
  caughtException = False

  try:
    n.initialize()
  except:
    caughtException = True
    print "Got exception as expected"

  assert caughtException

  # Test Dimensions
  level1SP.dimensions = engine.Dimensions([4,4])
  print "Set dimensions of level1SP to %s" % str(level1SP.dimensions)

  n.initialize()

  # Test Array
  a = engine.Array('Int32', 10)
  assert a.getType() == 'Int32'
  assert len(a) == 10
  import nupic
  assert type(a) == nupic.bindings.engine_internal.Int32Array

  for i in range(len(a)):
    a[i] = i

  for i in range(len(a)):
    assert type(a[i]) == int, "type(a) is %s expected int" % type(a)
    assert a[i] == i
    print i,
  print

  # --- Test Numpy Array
  print 'Testing Numpy Array'
  a = engine.Array('Byte', 15)
  print len(a)
  for i in range(len(a)):
    a[i] = ord('A') + i

  for i in range(len(a)):
    print a[i], ord('A') + i
    assert ord(a[i]) == ord('A') + i
  print

  print 'before asNumpyarray()'
  na = a.asNumpyArray()
  print 'after asNumpyarray()'

  assert na.shape == (15,)
  print 'na.shape:', na.shape
  na = na.reshape(5,3)
  assert na.shape == (5, 3)
  print 'na.shape:', na.shape
  for i in range(5):
    for j in range(3):
      print chr(na[i,j]), ' ',
    print
  print


  # --- Test get/setParameter for Int64 and Real64
  print '---'
  print 'Testing get/setParameter for Int64/Real64'
  val = level1SP.getParameterInt64('int64Param')
  rval = level1SP.getParameterReal64('real64Param')
  print 'level1SP.int64Param = ', val
  print 'level1SP.real64Param = ', rval

  val = 20
  level1SP.setParameterInt64('int64Param', val)
  val = 0
  val = level1SP.getParameterInt64('int64Param')
  print 'level1SP.int64Param = ', val, ' after setting to 20'

  rval = 30.1
  level1SP.setParameterReal64('real64Param', rval)
  rval = 0.0
  rval = level1SP.getParameterReal64('real64Param')
  print 'level1SP.real64Param = ', rval, ' after setting to 30.1'

  # --- Test array parameter
  # Array a will be allocated inside getParameter
  print '---'
  print 'Testing get/setParameterArray'
  a = engine.Array('Int64', 4)
  level1SP.getParameterArray("int64ArrayParam", a);
  print 'level1SP.int64ArrayParam size = ', len(a)
  print 'level1SP.int64ArrayParam = [ ',
  for i in range(len(a)):
    print a[i],

  print ']'
  #
  # --- test setParameter of an Int64 Array ---
  print 'Setting level1SP.int64ArrayParam to [ 1 2 3 4 ]'
  a2 = engine.Array('Int64', 4)
  for i in range(4):
    a2[i] = i + 1

  level1SP.setParameterArray('int64ArrayParam', a2);

  # get the value of int64ArrayParam after the setParameter call.
  # The array a owns its buffer, so we can call releaseBuffer if we
  # want, but the buffer should be reused if we just pass it again.
  #// a.releaseBuffer();
  level1SP.getParameterArray('int64ArrayParam', a)
  print 'level1SP.int64ArrayParam size = ', len(a)
  print 'level1SP.int64ArrayParam = [ ',
  for i in range(len(a)):
    print a[i],
  print ']'

  level1SP.compute()

  print "Running for 2 iteraitons"
  n.run(2)


  # --- Test input/output access
  #
  # Getting access via zero-copy
  try:
    level1SP.getOutputData('doesnotexist')
    assert False
  except:
    pass

  output = level1SP.getOutputData('bottomUpOut')
  print 'Element count in bottomUpOut is ', len(output)
  # set the actual output
  output[11] = 7777
  output[12] = 54321


  # Create a reshaped view of the numpy array
  # original output is 32x1 -- 16 nodes, 2 elements per node
  # Reshape to 8 rows, 4 columns
  numpy_output2 = output.reshape(8, 4)

  # Make sure the original output, the numpy array and the reshaped numpy view
  # are all in sync and access the same underlying memory.
  numpy_output2[1,0] = 5555
  assert output[4] == 5555

  output[5] = 3333
  assert numpy_output2[1, 1] == 3333
  numpy_output2[1,2] = 4444

  # --- Test doc strings
  # TODO: commented out because I'm not sure what to do with these
  # now that regions have been converted to the Collection class.
  # print
  # print "Here are some docstrings for properties and methods:"
  # for name in ('regionCount', 'getRegionCount', 'getRegionByName'):
  #   x = getattr(engine.Network, name)
  #   if isinstance(x, property):
  #     print 'property Network.{0}: "{1}"'.format(name, x.__doc__)
  #   else:
  #     print 'method Network.{0}(): "{1}"'.format(name, x.__doc__)

  # Typed methods should return correct type
  print "real64Param: %.2f" % level1SP.getParameterReal64("real64Param")

  # Uncomment to get performance for getParameter

  if 0:
    import time
    t1 = time.time()
    t1 = time.time()
    for i in xrange(0, 1000000):
      # x = level1SP.getParameterInt64("int64Param")   # buffered
      x = level1SP.getParameterReal64("real64Param")   # unbuffered
    t2 = time.time()

    print "Time for 1M getParameter calls: %.2f seconds" % (t2 - t1)

def test_two_region_network():
  n = engine.Network()

  region1 = n.addRegion("region1", "TestNode", "")
  region2 = n.addRegion("region2", "TestNode", "")

  names = []
  for name in n.regions:
    names.append(name)
  assert names == ['region1', 'region2']
  print n.getPhases('region1')
  assert n.getPhases('region1') == (0,)
  assert n.getPhases('region2') == (1,)

  n.link("region1", "region2", "TestFanIn2", "")

  print "Initialize should fail..."
  try:
    n.initialize()
    assert False
  except:
    pass

  print "Setting region1 dims"
  r1dims = engine.Dimensions([6,4])
  region1.setDimensions(r1dims)

  print "Initialize should now succeed"
  n.initialize()

  r2dims = region2.dimensions
  assert len(r2dims) == 2
  assert r2dims[0] == 3
  assert r2dims[1] == 2

  # Negative test
  try:
    region2.setDimensions(r1dims)
    assert False
  except:
    pass

def test_inputs_and_outputs():
  n = engine.Network()

  region1 = n.addRegion("region1", "TestNode", "")
  region2 = n.addRegion("region2", "TestNode", "")
  region1.setDimensions(engine.Dimensions([6,4]))
  n.link("region1", "region2", "TestFanIn2", "")
  n.initialize()

  r1_output = region1.getOutputData("bottomUpOut")

  region1.compute()
  print "Region 1 output after first iteration:"
  print "r1_output:", r1_output

  region2.prepareInputs()
  r2_input = region2.getInputData("bottomUpIn")
  print "Region 2 input after first iteration:"
  print 'r2_input:', r2_input

def test_node_spec():
  n = engine.Network()
  r = n.addRegion("region", "TestNode", "")

  print r.getSpec()

def test_pynode_get_set_parameter():
  n = engine.Network()

  r = n.addRegion("region", "py.TestNode", "")

  print "Setting region1 dims"
  r.dimensions = engine.Dimensions([6,4])

  print "Initialize should now succeed"
  n.initialize()

  result = r.getParameterReal64('real64Param')
  assert result == 64.1

  r.setParameterReal64('real64Param', 77.7)

  result = r.getParameterReal64('real64Param')
  assert result == 77.7

def test_pynode_get_node_spec():
  n = engine.Network()

  r = n.addRegion("region", "py.TestNode", "")

  print "Setting region1 dims"
  r.setDimensions(engine.Dimensions([6,4]))

  print "Initialize should now succeed"
  n.initialize()

  ns = r.spec

  assert len(ns.inputs) == 1
  i = ns.inputs['bottomUpIn']
  assert i.description == 'Primary input for the node'

  assert len(ns.outputs) == 1
  i = ns.outputs['bottomUpOut']
  assert i.description == 'Primary output for the node'

def test_two_region_pynode_network():
  n = engine.Network()

  region1 = n.addRegion("region1", "py.TestNode", "")
  region2 = n.addRegion("region2", "py.TestNode", "")

  n.link("region1", "region2", "TestFanIn2", "")

  print "Initialize should fail..."
  try:
    n.initialize()
    assert False
  except:
    pass

  print "Setting region1 dims"
  r1dims = engine.Dimensions([6,4])
  region1.setDimensions(r1dims)

  print "Initialize should now succeed"
  n.initialize()

  r2dims = region2.dimensions
  assert len(r2dims) == 2
  assert r2dims[0] == 3
  assert r2dims[1] == 2

def test_image_sensor():
  n = engine.Network()

  r = n.addRegion('r', 'py.ImageSensor', '{width: 4, height: 4}')
  r.setDimensions(engine.Dimensions([4, 4]))

  imagePath = 'bed.bmp'
  if not os.path.isfile(imagePath):
    imagePath = os.path.join(os.environ['NTA_ROOTDIR'],
                              'share/vision/data/pictures/clean/bed/bed.bmp')
    assert os.path.isfile(imagePath), imagePath + " Doesn't exist"

  r.executeCommand(['loadSingleImage', imagePath])
  n.run(1)

def test_knn_classifier():
  n = engine.Network()

  r = n.addRegion('r', 'py.KNNClassifierRegion', '{k: 3, maxCategoryCount: 2}')

  #n.run(1)

def main():
  test_errorHandling()
  test_getSpecFromType()
  test_one_region_network()
  test_two_region_network()
  test_inputs_and_outputs()
  test_node_spec()
  test_pynode_get_set_parameter()
  test_pynode_get_node_spec()
  test_two_region_pynode_network()
  #test_image_sensor()
  test_knn_classifier()

  print "Done -- all tests passed"

if __name__=='__main__':
  main()