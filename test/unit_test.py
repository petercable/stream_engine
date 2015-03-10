import base64
import os
import unittest
import msgpack
import numpy
from engine import app
from model.preload import Parameter, Stream
from util.cassandra_query import DataParameter, msgpack_one, FunctionParameter, build_func_map, execute_one_dpa, \
    StreamRequest, execute_dpas, msgpack_all
from util.preload_insert import create_db

import sys

sys.path.append('../ion-functions')

from ion_functions.data import ctd_functions, sfl_functions


class StreamUnitTestMixin(object):
    subsite = 'SUBSITE'
    node = 'NODE'
    sensor = 'SENSOR'
    method = 'METHOD'
    stream = 'STREAM'

    ctdpf_ckl_seawater_pressure_items = {
        'pressure': DataParameter(subsite, node, sensor, stream, method, Parameter.query.get(195)),
        'ctdpf_ckl_seawater_pressure': FunctionParameter(subsite, node, sensor, stream,
                                                         method, Parameter.query.get(1959)),
    }

    def get_ctdpf_ckl_items(self):
        parameters = Stream.query.filter(Stream.name == 'ctdpf_ckl_wfp_instrument_recovered').first().parameters
        temperature = DataParameter(self.subsite, self.node, self.sensor,
                                    self.stream, self.method, Parameter.query.get(193))
        conductivity = DataParameter(self.subsite, self.node, self.sensor,
                                     self.stream, self.method, Parameter.query.get(194))
        pressure = DataParameter(self.subsite, self.node, self.sensor,
                                 self.stream, self.method, Parameter.query.get(195))
        ctdpf_ckl_seawater_pressure = FunctionParameter(self.subsite, self.node, self.sensor,
                                                        self.stream, self.method, Parameter.query.get(1959))
        ctdpf_ckl_seawater_temperature = FunctionParameter(self.subsite, self.node, self.sensor,
                                                           self.stream, self.method, Parameter.query.get(1960))
        ctdpf_ckl_seawater_conductivity = FunctionParameter(self.subsite, self.node, self.sensor,
                                                            self.stream, self.method, Parameter.query.get(1961))
        ctdpf_ckl_sci_water_pracsal = FunctionParameter(self.subsite, self.node, self.sensor,
                                                        self.stream, self.method, Parameter.query.get(1962))
        ctdpf_ckl_seawater_density = FunctionParameter(self.subsite, self.node, self.sensor,
                                                       self.stream, self.method, Parameter.query.get(1963))

        temperature.data = numpy.array([254779, 254779, 254779])
        conductivity.data = numpy.array([6792, 6792, 6792])
        pressure.data = numpy.array([1003, 1003, 1003])

        stream_request = StreamRequest(self.subsite, self.node, self.sensor, self.method, self.stream, parameters)
        stream_request.data = [temperature, conductivity, pressure]
        stream_request.functions = [ctdpf_ckl_seawater_pressure, ctdpf_ckl_seawater_temperature,
                                    ctdpf_ckl_seawater_conductivity, ctdpf_ckl_sci_water_pracsal,
                                    ctdpf_ckl_seawater_density]

        coefficients = {'CC_latitude': 1.0, 'CC_longitude': 1.0}

        return stream_request, coefficients

    def create_stream_request(self, stream_name):
        parameters = Stream.query.filter(Stream.name == stream_name).first().parameters
        stream_request = StreamRequest(self.subsite, self.node, self.sensor, self.method, self.stream, parameters)
        for parameter in parameters:
            stream_request.add_parameter(parameter, self.subsite, self.node, self.sensor, stream_name, self.method)

        return stream_request

    def get_thsph_sample_data(self):
        # tc_rawdec_H
        return numpy.array([

        ])

    def get_thsph_stream_request(self):
        stream_request = self.create_stream_request('thsph_sample')
        data_map = stream_request.get_data_map()

        test_array = self.get_thsph_sample_data()

    def get_trhph_sample_data(self):
        #   V_ts, V_tc, T_ts, T, V, ORP, v_r1, v_r2, v_r3, temp, chl [mmol/kg]
        return numpy.array([
            [1.506,	0.000,	12.01,	12.0,  1.806,   -50., 0.440,  4.095,  4.095,  105.4,    59.0],
            [1.479,	0.015,	12.67,	17.1,  1.541,  -116., 0.320,  4.095,  4.095,  374.2,    60.0],
            [1.926,	0.001,	2.47,	2.1,   1.810,   -48., 0.184,  0.915,  4.064,  105.4,   175.0],
            [1.932,	0.274,	2.34,	69.5,  0.735,  -317., 0.198,  1.002,  4.095,  241.9,    71.0],
            [1.927,	0.306,	2.45,	77.5,  0.745,  -315., 0.172,  0.857,  4.082,  374.2,   132.0],
        ])

    def get_trhph_stream_request(self):
        stream_request = self.create_stream_request('trhph_sample')
        data_map = stream_request.get_data_map()

        test_array = self.get_trhph_sample_data()

        data_map.get(428).data = test_array[:, 0]
        data_map.get(430).data = test_array[:, 1]
        data_map.get(427).data = test_array[:, 4]
        data_map.get(421).data = test_array[:, 6]
        data_map.get(422).data = test_array[:, 7]
        data_map.get(423).data = test_array[:, 8]

        # TODO - engine should stretch these calibration coefficients
        coefficients = {'CC_ts_slope': numpy.tile(0.003, data_map.get(428).data.shape),
                        'CC_tc_slope': numpy.tile(4.22e-5, data_map.get(428).data.shape),
                        'CC_gain': 4.0,
                        'CC_offset': 2004.0}
        return stream_request, coefficients


class StreamUnitTest(unittest.TestCase, StreamUnitTestMixin):
    def setUp(self):
        if not os.path.exists(app.config['DBFILE_LOCATION']):
            create_db()

    def tearDown(self):
        pass

    def test_parameters(self):
        """
        Test whether we can retrieve a parameter by id and verify that
        it contains the correct data.
        :return:
        """
        pmap = {
            195: {
                'name': 'pressure',
                'ptype': 'quantity',
                'encoding': 'int32',
                'needs': [195],
                'cc': [],
            },
            1963: {
                'name': 'ctdpf_ckl_seawater_density',
                'ptype': 'function',
                'encoding': 'float32',
                'needs': [193, 194, 195, 1959, 1960, 1961, 1962, 1963],
                'cc': ['CC_latitude', 'CC_longitude'],
            },
        }

        # by id
        for pdid in pmap:
            parameter = Parameter.query.get(pdid)
            self.assertIsNotNone(parameter)
            self.assertEqual(parameter.name, pmap[pdid]['name'])
            self.assertEqual(parameter.id, pdid)
            self.assertEqual(parameter.parameter_type.value, pmap[pdid]['ptype'])
            self.assertEqual(parameter.value_encoding.value, pmap[pdid]['encoding'])
            self.assertEqual(sorted([p.id for p in parameter.needs()]), pmap[pdid]['needs'])
            self.assertEqual(sorted(parameter.needs_cc()), pmap[pdid]['cc'])

            # by name (FAILS, parameter names are not unique!)
            # for pdid in pmap:
            # parameter = Parameter.query.filter(Parameter.name == pmap[pdid]['name']).first()
            #     self.assertIsNotNone(parameter)
            #     self.assertEqual(parameter.name, pmap[pdid]['name'])
            #     self.assertEqual(parameter.id, pdid)
            #     self.assertEqual(parameter.parameter_type.value, pmap[pdid]['ptype'])
            #     self.assertEqual(parameter.value_encoding.value, pmap[pdid]['encoding'])
            #     self.assertEqual(sorted([p.id for p in parameter.needs()]), pmap[pdid]['needs'])
            #     self.assertEqual(sorted(parameter.needs_cc()), pmap[pdid]['cc'])

    def test_streams(self):
        """
        Test if we can retrieve a stream by name and verify that it contains
        the correct parameters.
        :return:
        """
        stream = Stream.query.filter(Stream.name == 'thsph_sample').first()
        self.assertEqual(stream.name, 'thsph_sample')
        self.assertEqual([p.id for p in stream.parameters],
                         [7, 10, 11, 12, 863, 2260, 2261, 2262, 2263,
                          2264, 2265, 2266, 2267, 2624, 2625, 2626,
                          2627, 2628, 2629, 2630, 2631, 2632, 2633, 2634, 2635])

    def test_msgpack(self):
        """
        Create a DataParameter, msgpack it, then verify we can retrieve the
        original message contents.
        :return:
        """
        parameter = Parameter.query.get(193)
        p = DataParameter(self.subsite, self.node, self.sensor, self.stream, self.method, parameter)
        p.data = numpy.array([[1, 2, 3], [4, 5, 6]])
        p.shape = p.data.shape

        packed = msgpack_one(p)
        unpacked = msgpack.unpackb(base64.b64decode(packed['data']))
        self.assertTrue(numpy.array_equal(p.data, numpy.array(unpacked).reshape(p.shape)))

    def test_build_func_map(self):
        """
        Create a DataParameter and FunctionParameter and verify the correct set of arguments
        is generated.
        :return:
        """
        stream_request, coefficients = self.get_ctdpf_ckl_items()
        data_map = stream_request.get_data_map()

        dp = data_map.get(195)
        fp = data_map.get(1959)

        dp.data = numpy.array([1, 2, 3])
        kwargs = build_func_map(fp, {195: dp}, None)
        expected_kwargs = {'p0': dp.data}

        self.assertEqual(expected_kwargs, kwargs)

    def test_execute_one_dpa(self):
        """
        Create a DataParameter and FunctionParameter and verify the DPA output matches a direct call to the
        corresponding method from ion_functions.
        :return:
        """
        stream_request, coefficients = self.get_ctdpf_ckl_items()
        data_map = stream_request.get_data_map()

        dp = data_map.get(195)
        fp = data_map.get(1959)

        dp.data = numpy.array([1, 2, 3])
        kwargs = build_func_map(fp, {195: dp}, None)
        execute_one_dpa(fp, kwargs)

        self.assertTrue(numpy.array_equal(fp.data, ctd_functions.ctd_sbe52mp_preswat(dp.data)))

    def test_execute_dpas(self):
        """
        Execute multiple dependent DPAs on a single stream, compare output to directly computed results.
        :return:
        """
        # ctdpf_ckl
        stream_request, coefficients = self.get_ctdpf_ckl_items()
        data_map = stream_request.get_data_map()
        execute_dpas(stream_request, coefficients)

        expected_pressure = ctd_functions.ctd_sbe52mp_preswat(data_map.get(195).data)
        expected_temperature = ctd_functions.ctd_sbe52mp_tempwat(data_map.get(193).data)
        expected_conductivity = ctd_functions.ctd_sbe52mp_condwat(data_map.get(194).data)
        expected_pracsal = ctd_functions.ctd_pracsal(expected_conductivity, expected_temperature, expected_pressure)
        expected_density = ctd_functions.ctd_density(expected_pracsal, expected_temperature, expected_pressure,
                                                     coefficients['CC_latitude'], coefficients['CC_longitude'])

        self.assertTrue(numpy.array_equal(data_map.get(1959).data, expected_pressure))
        self.assertTrue(numpy.array_equal(data_map.get(1960).data, expected_temperature))
        self.assertTrue(numpy.array_equal(data_map.get(1961).data, expected_conductivity))
        self.assertTrue(numpy.array_equal(data_map.get(1962).data, expected_pracsal))
        self.assertTrue(numpy.array_equal(data_map.get(1963).data, expected_density))

        # trhph
        stream_request, coefficients = self.get_trhph_stream_request()
        data_map = stream_request.get_data_map()
        execute_dpas(stream_request, coefficients)
        expected_vfltemp = sfl_functions.sfl_trhph_vfltemp(data_map.get(428).data, data_map.get(430).data,
                                                   coefficients['CC_tc_slope'], coefficients['CC_ts_slope'])
        expected_vflchlor = sfl_functions.sfl_trhph_chloride(data_map.get(421).data, data_map.get(422).data,
                                                             data_map.get(423).data, expected_vfltemp)
        expected_vflorp = sfl_functions.sfl_trhph_vflorp(data_map.get(427).data, coefficients['CC_offset'],
                                                         coefficients['CC_gain'])
        expected_vflthermtemp = sfl_functions.sfl_trhph_vfl_thermistor_temp(data_map.get(428).data)

        self.assertTrue(numpy.array_equal(stream_request.get_data_map().get(965).data, expected_vfltemp))
        self.assertTrue(numpy.array_equal(stream_request.get_data_map().get(966).data, expected_vflchlor))
        self.assertTrue(numpy.array_equal(stream_request.get_data_map().get(967).data, expected_vflorp))
        self.assertTrue(numpy.array_equal(stream_request.get_data_map().get(2623).data, expected_vflthermtemp))


    def test_interpolate(self):
        """

        :return:
        """
        # thpsh_stream_request, thsph_coefficients = self.get_thsph_stream_request()
        # trhph_stream_request, trhph_coefficients = self.get_trhph_stream_request()
        pass