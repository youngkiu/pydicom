# -*- coding: utf-8 -*-
# Copyright 2008-2019 pydicom authors. See LICENSE file for details.
import json

import pytest

from pydicom import dcmread
from pydicom.data import get_testdata_file
from pydicom.dataelem import DataElement
from pydicom.dataset import Dataset
from pydicom.tag import Tag, BaseTag
from pydicom.valuerep import PersonName


class TestPersonName:
    def test_json_pn_from_file(self):
        with open(get_testdata_file("test_PN.json")) as s:
            ds = Dataset.from_json(s.read())
        assert isinstance(ds[0x00080090].value, PersonName)
        assert isinstance(ds[0x00100010].value, PersonName)
        inner_seq = ds[0x04000561].value[0][0x04000550]
        dataelem = inner_seq[0][0x00100010]
        assert isinstance(dataelem.value, PersonName)

    def test_pn_components_to_json(self):
        def check_name(tag, components):
            # we cannot directly compare the dictionaries, as they are not
            # guaranteed insertion-ordered in Python < 3.7
            value = ds_json[tag]['Value']
            assert 1 == len(value)
            value = value[0]
            if len(components) == 3:
                assert components[2] == value['Phonetic']
            else:
                assert 'Phonetic' not in value
            if len(components) >= 2:
                assert components[1] == value['Ideographic']
            else:
                assert 'Ideographic' not in value
            assert components[0] == value['Alphabetic']

        ds = Dataset()
        ds.add_new(0x00100010, 'Yamada^Tarou=山田^太郎=やまだ^たろう', VR='PN')
        ds.add_new(0x00091001, 'Yamada^Tarou', VR='PN')
        ds.add_new(0x00091002, 'Yamada^Tarou==', VR='PN')
        ds.add_new(0x00091003, '=山田^太郎=やまだ^たろう', VR='PN')
        ds.add_new(0x00091004, 'Yamada^Tarou==やまだ^たろう', VR='PN')
        ds.add_new(0x00091005, '==やまだ^たろう', VR='PN')
        ds.add_new(0x00091006, '=山田^太郎', VR='PN')
        ds.add_new(0x00091007, 'Yamada^Tarou=山田^太郎', VR='PN')
        ds_json = ds.to_json_dict()
        check_name('00100010', ['Yamada^Tarou', '山田^太郎', 'やまだ^たろう'])
        check_name('00091001', ['Yamada^Tarou'])
        check_name('00091002', ['Yamada^Tarou'])
        check_name('00091003', ['', '山田^太郎', 'やまだ^たろう'])
        check_name('00091004', ['Yamada^Tarou', '', 'やまだ^たろう'])
        check_name('00091005', ['', '', 'やまだ^たろう'])
        check_name('00091006', ['', '山田^太郎'])
        check_name('00091007', ['Yamada^Tarou', '山田^太郎'])

    def test_pn_components_from_json(self):
        # this is the encoded dataset from the previous test, with some
        # empty components omitted
        ds_json = ('{"00100010": {"vr": "PN", "Value": [{"Alphabetic": '
                   '"Yamada^Tarou", "Ideographic": "山田^太郎", '
                   '"Phonetic": "やまだ^たろう"}]}, '
                   '"00091001": {"vr": "PN", "Value": '
                   '[{"Alphabetic": "Yamada^Tarou"}]}, '
                   '"00091002": {"vr": "PN", "Value": '
                   '[{"Alphabetic": "Yamada^Tarou", "Ideographic": "", '
                   '"Phonetic": ""}]}, '
                   '"00091003": {"vr": "PN", "Value": [{'
                   '"Ideographic": "山田^太郎", '
                   '"Phonetic": "やまだ^たろう"}]}, '
                   '"00091004": {"vr": "PN", "Value": '
                   '[{"Alphabetic": "Yamada^Tarou", '
                   '"Phonetic": "やまだ^たろう"}]}, '
                   '"00091005": {"vr": "PN", "Value": '
                   '[{"Phonetic": "やまだ^たろう"}]}, '
                   '"00091006": {"vr": "PN", "Value":'
                   ' [{"Ideographic": "山田^太郎"}]}, '
                   '"00091007": {"vr": "PN", "Value": '
                   '[{"Alphabetic": "Yamada^Tarou", '
                   '"Ideographic": "山田^太郎"}]}}')

        ds = Dataset.from_json(ds_json)
        assert 'Yamada^Tarou=山田^太郎=やまだ^たろう' == ds.PatientName
        assert 'Yamada^Tarou' == ds[0x00091001].value
        assert 'Yamada^Tarou' == ds[0x00091002].value
        assert '=山田^太郎=やまだ^たろう' == ds[0x00091003].value
        assert 'Yamada^Tarou==やまだ^たろう' == ds[0x00091004].value
        assert '==やまだ^たろう' == ds[0x00091005].value
        assert '=山田^太郎' == ds[0x00091006].value
        assert 'Yamada^Tarou=山田^太郎' == ds[0x00091007].value

    def test_empty_value(self):
        ds = Dataset()
        ds.add_new(0x00100010, '')
        ds_json = ds.to_json_dict()
        assert '00100010' in ds_json
        assert 'Value' not in ds_json['00100010']

    def test_multi_value_to_json(self):
        ds = Dataset()
        patient_names = ['Buc^Jérôme', 'Διονυσιος', 'Люкceмбypг']
        ds.add_new(0x00091001, patient_names, VR='PN')
        ds_json = ds.to_json_dict()
        assert [{'Alphabetic': 'Buc^Jérôme'},
                {'Alphabetic': 'Διονυσιος'},
                {'Alphabetic': 'Люкceмбypг'}] == ds_json['00091001']['Value']

    def test_dataelem_from_json(self):
        tag = 0x0080090
        vr = "PN"
        value = [{"Alphabetic": ""}]
        dataelem = DataElement.from_json(Dataset, tag, vr, value, "Value")
        assert isinstance(dataelem.value, PersonName)


class TestAT:
    def test_to_json(self):
        ds = Dataset()
        ds.add_new(0x00091001, [0x00100010, 0x00100020], VR='AT')
        ds.add_new(0x00091002, Tag(0x28, 0x02), VR='AT')
        ds.add_new(0x00091003, BaseTag(0x00280002), VR='AT')
        ds.add_new(0x00091004, [0x00280002, Tag('PatientName')], VR='AT')
        ds_json = ds.to_json_dict()

        assert ['00100010', '00100020'] == ds_json['00091001']['Value']
        assert ['00280002'] == ds_json['00091002']['Value']
        assert ['00280002'] == ds_json['00091003']['Value']
        assert ['00280002', '00100010'] == ds_json['00091004']['Value']

    def test_from_json(self):
        ds_json = ('{"00091001": {"vr": "AT", "Value": ["000910AF"]}, '
                   '"00091002": {"vr": "AT", "Value": ["00100010", '
                   '"00100020", "00100030"]}}')
        ds = Dataset.from_json(ds_json)
        assert 0x000910AF == ds[0x00091001].value
        assert [0x00100010, 0x00100020, 0x00100030] == ds[0x00091002].value

    def test_invalid_value_in_json(self):
        ds_json = ('{"00091001": {"vr": "AT", "Value": ["000910AG"]}, '
                   '"00091002": {"vr": "AT", "Value": ["00100010"]}}')
        with pytest.warns(UserWarning, match='Invalid value "000910AG" for '
                                             'AT element - ignoring it'):
            ds = Dataset.from_json(ds_json)
            assert ds[0x00091001].value is None
            assert 0x00100010 == ds[0x00091002].value

    def test_invalid_tag_in_json(self):
        ds_json = ('{"000910AG": {"vr": "AT", "Value": ["00091000"]}, '
                   '"00091002": {"vr": "AT", "Value": ["00100010"]}}')
        with pytest.raises(ValueError, match="Data element '000910AG' could "
                                             "not be loaded from JSON:"):
            ds = Dataset.from_json(ds_json)
            assert ds[0x00091001].value is None
            assert 0x00100010 == ds[0x00091002].value


class TestDataSetToJson:
    def test_json_from_dicom_file(self, no_numpy_use):
        ds1 = Dataset(dcmread(get_testdata_file("CT_small.dcm")))
        ds_json = ds1.to_json()
        ds2 = Dataset.from_json(ds_json)
        assert ds1 == ds2

        ds_json = ds1.to_json_dict()
        ds2 = Dataset.from_json(ds_json)
        assert ds1 == ds2

    def test_roundtrip(self):
        ds = Dataset()
        ds.add_new(0x00080005, 'ISO_IR 100', VR='CS')
        ds.add_new(0x00090010, 'Creator 1.0', VR='LO')
        ds.add_new(0x00091001, 'Version1', VR='SH')
        ds.add_new(0x00091002, b'BinaryContent', VR='OB')
        ds.add_new(0x00091003, b'\x0102\x3040\x5060', VR='OW')
        ds.add_new(0x00091004, b'\x00\x01\x02\x03\x04\x05\x06\x07', VR='OF')
        ds.add_new(0x00091005, b'\x00\x01\x02\x03\x04\x05\x06\x07'
                               b'\x01\x01\x02\x03\x04\x05\x06\x07', VR='OD')
        ds.add_new(0x00091006, b'\x00\x01\x02\x03\x04\x05\x06\x07'
                               b'\x01\x01\x02\x03', VR='OL')
        ds.add_new(0x00091007, '1.2.3.4.5.6', VR='UI')
        ds.add_new(0x00091008, '20200101', VR='DA')
        ds.add_new(0x00091009, '115500', VR='TM')
        ds.add_new(0x0009100a, '20200101115500.000000', VR='DT')
        ds.add_new(0x0009100b, 3000000000, VR='UL')
        ds.add_new(0x0009100c, -2000000000, VR='SL')
        ds.add_new(0x0009100d, 40000, VR='US')
        ds.add_new(0x0009100e, -22222, VR='SS')
        ds.add_new(0x0009100f, 3.14, VR='FL')
        ds.add_new(0x00091010, 3.14159265, VR='FD')
        ds.add_new(0x00091011, 'TEST MODE', VR='CS')
        ds.add_new(0x00091012, 'CITIZEN^1', VR='PN')
        ds.add_new(0x00091013, 'Yamada^Tarou=山田^太郎=やまだ^たろう', VR='PN')
        ds.add_new(0x00091014, '42', VR='IS')
        ds.add_new(0x00091015, '3.14159265', VR='DS')
        ds.add_new(0x00091016, b'CONQUESTSRV1', VR='AE')
        ds.add_new(0x00091017, '055Y', VR='AS')
        ds.add_new(0x00091018, 50 * 'Калинка,', VR='LT')
        ds.add_new(0x00091019, 'LONG CODE VALUE', VR='UC')
        ds.add_new(0x0009101a, b'\x0102\x3040\x5060', VR='UN')
        ds.add_new(0x0009101b, 'https://example.com', VR='UR')
        ds.add_new(0x0009101c, [0x00100010, 0x00100020], VR='AT')
        ds.add_new(0x0009101d, 100 * 'علي بابا', VR='ST')
        ds.add_new(0x0009101e, 'Διονυσιος', VR='SH')
        ds.add_new(0x00090011, 'Creator 2.0', VR='LO')
        ds.add_new(0x00091101, 'Version2', VR='SH')
        ds.add_new(0x00091102, 2, VR='US')

        json_string = ds.to_json()
        json_model = json.loads(json_string)

        assert json_model['00080005']['Value'] == ['ISO_IR 100']
        assert json_model['00091007']['Value'] == ['1.2.3.4.5.6']
        assert json_model['0009100A']['Value'] == ['20200101115500.000000']
        assert json_model['0009100B']['Value'] == [3000000000]
        assert json_model['0009100C']['Value'] == [-2000000000]
        assert json_model['0009100D']['Value'] == [40000]
        assert json_model['0009100F']['Value'] == [3.14]
        assert json_model['00091010']['Value'] == [3.14159265]
        assert json_model['00091018']['Value'] == [50 * 'Калинка,']

        ds2 = Dataset.from_json(json_string)
        assert ds == ds2
        ds2 = Dataset.from_json(json_model)
        assert ds == ds2

        json_model2 = ds.to_json_dict()

        assert json_model == json_model2

    def test_dataset_dumphandler(self):
        ds = Dataset()
        ds.add_new(0x00100010, 'Jane^Doe')
        # as the order of the keys is not defined, we have to check both
        assert ds.to_json() in ('{"00100010": {"vr": "PN", "Value": [{'
                                '"Alphabetic": "Jane^Doe"}]}}',
                                '{"00100010": {"Value": [{'
                                '"Alphabetic": "Jane^Doe"}], "vr": "PN"}}')

        assert {
                   "00100010": {
                       "vr": "PN", "Value": [{"Alphabetic": "Jane^Doe"}]}
               } == ds.to_json(dump_handler=lambda d: d)

    def test_dataelement_dumphandler(self):
        element = DataElement(0x00100010, 'PN', 'Jane^Doe')
        # as the order of the keys is not defined, we have to check both
        assert element.to_json() in ('{"vr": "PN", "Value": [{'
                                     '"Alphabetic": "Jane^Doe"}]}',
                                     '{"Value": [{'
                                     '"Alphabetic": "Jane^Doe"}], "vr": "PN"}')

        assert {
                   "vr": "PN", "Value": [{"Alphabetic": "Jane^Doe"}]
               } == element.to_json(dump_handler=lambda d: d)

    def test_sort_order(self):
        """Test that tags are serialized in ascending order."""
        ds = Dataset()
        ds.add_new(0x00100040, 'F')
        ds.add_new(0x00100030, '20000101')
        ds.add_new(0x00100020, '0017')
        ds.add_new(0x00100010, 'Jane^Doe')

        ds_json = ds.to_json()
        assert ds_json.index('"00100010"') < ds_json.index('"00100020"')
        assert ds_json.index('"00100020"') < ds_json.index('"00100030"')
        assert ds_json.index('"00100030"') < ds_json.index('"00100040"')


class TestSequence:
    def test_nested_sequences(self):
        test1_json = get_testdata_file("test1.json")
        with open(test1_json) as f:
            with pytest.warns(UserWarning,
                              match='no bulk data URI handler provided '):
                ds = Dataset.from_json(f.read())
            del ds.PixelData
        ds2 = Dataset.from_json(ds.to_json())
        assert ds == ds2


class TestBinary:
    def test_inline_binary(self):
        ds = Dataset()
        ds.add_new(0x00091002, b'BinaryContent', VR='OB')
        ds_json = ds.to_json_dict()
        assert "00091002" in ds_json
        assert "QmluYXJ5Q29udGVudA==" == ds_json["00091002"]["InlineBinary"]
        ds1 = Dataset.from_json(ds_json)
        assert ds == ds1
        # also test if the binary is enclosed in a list
        ds_json["00091002"]["InlineBinary"] = ["QmluYXJ5Q29udGVudA=="]
        ds1 = Dataset.from_json(ds_json)
        assert ds == ds1

    def test_invalid_inline_binary(self):
        msg = ('"InlineBinary" of data element "00091002" '
               'must be a bytes-like object.')
        ds_json = '{"00091002": {"vr": "OB", "InlineBinary": 42}}'
        with pytest.raises(TypeError, match=msg):
            Dataset.from_json(ds_json)

        ds_json = '{"00091002": {"vr": "OB", "InlineBinary": [42]}}'
        with pytest.raises(TypeError, match=msg):
            Dataset.from_json(ds_json)

    def test_valid_bulkdata_uri(self):
        ds_json = ('{"00091002": {"vr": "OB", "BulkDataURI": '
                   '"http://example.com/bulkdatahandler"}}')
        msg = r"no bulk data URI handler provided"
        with pytest.warns(UserWarning, match=msg):
            ds = Dataset.from_json(ds_json)
        assert 0x00091002 in ds

        ds_json = ('{"00091002": {"vr": "OB", "BulkDataURI": '
                   '["http://example.com/bulkdatahandler"]}}')
        with pytest.warns(UserWarning, match=msg):
            ds = Dataset.from_json(ds_json)
        assert 0x00091002 in ds

    def test_invalid_bulkdata_uri(self):
        msg = ('"BulkDataURI" of data element "00091002" '
               'must be a string.')
        ds_json = '{"00091002": {"vr": "OB", "BulkDataURI": 42}}'
        with pytest.raises(TypeError, match=msg):
            Dataset.from_json(ds_json)

        ds_json = '{"00091002": {"vr": "OB", "BulkDataURI": [42]}}'
        with pytest.raises(TypeError, match=msg):
            Dataset.from_json(ds_json)

    def test_bulk_data_reader_is_called(self):
        def bulk_data_reader(value):
            return b'xyzzy'

        json_data = {
            "00091002": {"vr": "OB", "BulkDataURI": "https://a.dummy.url"}
        }
        ds = Dataset().from_json(json.dumps(json_data), bulk_data_reader)

        assert b'xyzzy' == ds[0x00091002].value

    def test_bulk_data_reader_is_called_2(self):
        def bulk_data_reader(tag, vr, value):
            return b'xyzzy'

        json_data = {
            "00091002": {"vr": "OB", "BulkDataURI": "https://a.dummy.url"}
        }
        ds = Dataset().from_json(json.dumps(json_data), bulk_data_reader)

        assert b'xyzzy' == ds[0x00091002].value

    def test_bulk_data_reader_is_called_within_SQ(self):
        def bulk_data_reader(_):
            return b'xyzzy'

        json_data = {
            "003a0200": {
                "vr": "SQ",
                "Value": [
                    {
                        "54001010": {
                            "vr": "OW",
                            "BulkDataURI": "https://a.dummy.url"
                        }
                    }
                ]
            }
        }

        ds = Dataset().from_json(json.dumps(json_data), bulk_data_reader)

        assert b'xyzzy' == ds[0x003a0200].value[0][0x54001010].value


class TestNumeric:
    def test_numeric_values(self):
        ds = Dataset()

        ds.add_new(0x0009100b, 3000000000, VR='UL')
        ds.add_new(0x0009100c, -2000000000, VR='SL')
        ds.add_new(0x0009100d, 40000, VR='US')
        ds.add_new(0x0009100e, -22222, VR='SS')
        ds.add_new(0x0009100f, 3.14, VR='FL')
        ds.add_new(0x00091010, 3.14159265, VR='FD')
        ds.add_new(0x00091014, '42', VR='IS')
        ds.add_new(0x00091015, '3.14159265', VR='DS')
        ds.add_new(0x00091102, 2, VR='US')

        ds_json = ds.to_json_dict()

        assert ds_json['0009100B']['Value'] == [3000000000]
        assert ds_json['0009100C']['Value'] == [-2000000000]
        assert ds_json['0009100D']['Value'] == [40000]
        assert ds_json['0009100E']['Value'] == [-22222]
        assert ds_json['0009100F']['Value'] == [3.14]
        assert ds_json['00091010']['Value'] == [3.14159265]
        assert ds_json['00091014']['Value'] == [42]
        assert ds_json['00091015']['Value'] == [3.14159265]
        assert ds_json['00091102']['Value'] == [2]

    def test_numeric_types(self):
        ds = Dataset()

        ds.add_new(0x0009100b, 3000000000, VR='UL')
        ds.add_new(0x0009100c, -2000000000, VR='SL')
        ds.add_new(0x0009100d, 40000, VR='US')
        ds.add_new(0x0009100e, -22222, VR='SS')
        ds.add_new(0x0009100f, 3.14, VR='FL')
        ds.add_new(0x00091010, 3.14159265, VR='FD')
        ds.add_new(0x00091014, '42', VR='IS')
        ds.add_new(0x00091015, '3.14159265', VR='DS')
        ds.add_new(0x00091102, 2, VR='US')

        ds_json = ds.to_json_dict()

        assert type(ds_json['0009100B']['Value'][0]) == int
        assert type(ds_json['0009100C']['Value'][0]) == int
        assert type(ds_json['0009100D']['Value'][0]) == int
        assert type(ds_json['0009100E']['Value'][0]) == int
        assert type(ds_json['0009100F']['Value'][0]) == float
        assert type(ds_json['00091010']['Value'][0]) == float
        assert type(ds_json['00091014']['Value'][0]) == int
        assert type(ds_json['00091015']['Value'][0]) == float
        assert type(ds_json['00091102']['Value'][0]) == int
