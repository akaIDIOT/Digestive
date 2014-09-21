from os import path

from digestive.ewf import EWFSource, format_supported, list_ewf_files


here = path.dirname(path.abspath(__file__))


def test_format_supported():
    supported = ['file.S01', 'file.E01', 'file.e01', 'file.L01', 'file.Ex01', 'file.Lx01', 'file.tar.E01']
    not_supported = ['file.dd', 'file.raw', 'file.E1', 'file.Ex1', 'file.tar.gz', 'file.E01.raw']

    for supported in supported:
        assert format_supported(supported)

    for not_supported in not_supported:
        assert not format_supported(not_supported)


def test_list_ewf_files():
    files = {path.join(here, 'files/random.E01'), path.join(here, 'files/random.E02')}
    assert set(list_ewf_files(path.join(here, 'files/random.E01'))) == files
    # non-primary file is not handled as the beginning of a set
    assert list_ewf_files(path.join(here, 'files/random.E02')) == [path.join(here, 'files/random.E02')]


def test_ewf_source_simple():
    source = EWFSource(path.join(here, 'files/random.E01'))
    # random.E01 has two parts, should be visible
    assert str(source) == path.join(here, 'files/random.E01') + '..E02'
