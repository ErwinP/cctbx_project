from __future__ import absolute_import, division, print_function
from six.moves import range
from dials.array_family import flex
import math

class reflection_table_utils(object):

  @staticmethod
  def get_next_hkl_reflection_table(reflections):
    '''Generate asu hkl slices from an asu hkl-sorted reflection table'''
    if reflections.size() == 0:
      yield reflections

    i_begin = 0
    hkl_ref = reflections[0].get('miller_index_asymmetric')
    for i in range(reflections.size()):
      hkl = reflections[i].get('miller_index_asymmetric')
      if hkl == hkl_ref:
        continue
      else:
        yield reflections[i_begin:i]
        i_begin = i
        hkl_ref = hkl

    yield reflections[i_begin:i+1]

  @staticmethod
  def select_odd_experiment_reflections(reflections):
    'Select reflections from experiments with odd ids. An experiment id must be a string representing a hexadecimal number'
    sel = flex.bool()
    for refl in reflections:
      sel.append(int(refl['exp_id'], 16)%2 != 0)
    return reflections.select(sel)

  @staticmethod
  def select_even_experiment_reflections(reflections):
    'Select reflections from experiments with even ids. An experiment id must be a string representing a hexadecimal number'
    sel = flex.bool()
    for refl in reflections:
      sel.append(int(refl['exp_id'], 16)%2 == 0)
    return reflections.select(sel)

  @staticmethod
  def merged_reflection_table():
    '''Create a reflection table for storing merged HKLs'''
    table = flex.reflection_table()
    table['miller_index'] = flex.miller_index()
    table['intensity'] = flex.double()
    table['sigma'] = flex.double()
    table['multiplicity'] = flex.int()
    return table

  @staticmethod
  def merge_reflections(reflections, min_multiplicity):
    '''Merge intensities of multiply-measured symmetry-reduced HKLs'''
    merged_reflections = reflection_table_utils.merged_reflection_table()
    for refls in reflection_table_utils.get_next_hkl_reflection_table(reflections=reflections):
      if refls.size() == 0:
        break # unless the input "reflections" list is empty, generated "refls" lists cannot be empty

      hkl = refls[0]['miller_index_asymmetric']
      # This assert is timeconsuming when using a small number of cores
      #assert not (hkl in merged_reflections['miller_index']) # i.e. assert that the input reflection table came in sorted

      refls = refls.select(refls['intensity.sum.variance'] > 0.0)

      if refls.size() >= min_multiplicity:
        weighted_intensity_array = refls['intensity.sum.value'] / refls['intensity.sum.variance']
        weights_array = flex.double(refls.size(), 1.0) / refls['intensity.sum.variance']

        weighted_mean_intensity = flex.sum(weighted_intensity_array) / flex.sum(weights_array)
        standard_error_of_weighted_mean_intensity = 1.0/math.sqrt(flex.sum(weights_array))

        merged_reflections.append(
                                  {'miller_index' : hkl,
                                  'intensity' : weighted_mean_intensity,
                                  'sigma' : standard_error_of_weighted_mean_intensity,
                                  'multiplicity' : refls.size()})
    return merged_reflections

  @staticmethod
  def prune_reflection_table_keys(reflections, keys_to_delete=None, keys_to_keep=None):
    '''Remove reflection table keys: either inclusive or exclusive'''
    if len(reflections) != 0:
      all_keys = list()
      for key in reflections[0]:
        all_keys.append(key)
      if keys_to_delete != None:
        for key in keys_to_delete:
          if key in all_keys:
            del reflections[key]
      elif keys_to_keep != None:
        for key in all_keys:
          #if not key in ['intensity.sum.value', 'intensity.sum.variance', 'miller_index', 'miller_index_asymmetric', 'exp_id', 'odd_frame', 's1']:
          if not key in keys_to_keep:
            del reflections[key]
    return reflections
