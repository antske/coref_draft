import pytest
import logging

from multisieve_coreference.constituency_tree import ConstituencyTree


@pytest.fixture
def example_constituency_tree(example_naf_object):
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    return ConstituencyTree.from_naf(example_naf_object)


@pytest.fixture
def sonar_constituency_tree(sonar_naf_object):
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    return ConstituencyTree.from_naf(sonar_naf_object)


@pytest.fixture
def deep_tree():
    return ConstituencyTree({
        't_1016': {('t_1017', 'hd/mod')},
        't_1017': {('t_1019', 'hd/obj1')},
        't_1019': {('t_1018', 'hd/mod')}
    })


@pytest.fixture(params=[10, 100, 1000, 10000])
def very_deep_tree(request):
    return ConstituencyTree({
        i: {(i + 1, None)} for i in range(request.param)
    })


@pytest.fixture(params=[
    'example_constituency_tree',
    'sonar_constituency_tree',
    'deep_tree'
])
def any_tree(request):
    return request.getfixturevalue(request.param)


def test_no_filter(example_constituency_tree):
    assert example_constituency_tree.head2deps == {
        't_1': {
            ('t_0', 'hd/su'),
            ('t_2', 'hd/obj1')
        }
    }
    assert example_constituency_tree.dep2heads == {
        't_0': {('t_1', 'hd/su')},
        't_2': {('t_1', 'hd/obj1')}
    }
    assert example_constituency_tree.get_constituent('t_1') == {
        't_0',
        't_1',
        't_2'
    }
    assert example_constituency_tree.get_constituent('t_0') == {'t_0'}
    assert example_constituency_tree.get_constituent('t_2') == {'t_2'}
    assert example_constituency_tree.get_constituent('very random') == \
        {'very random'}


def test_deep_get_constituent(deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    assert deep_tree.get_constituent('t_1016') == {
        't_1016',
        't_1017',
        't_1019',
        't_1018'
    }


def test_repr(any_tree):
    repr(any_tree)


def test_filter_top_node(example_constituency_tree, deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    tree = example_constituency_tree
    assert tree.filter_headdep_dict(tree.head2deps, lambda t: t != 't_1') == {}
    assert deep_tree.filter_headdep_dict(
        deep_tree.head2deps,
        lambda t: t != 't_1016'
    ) == {
        't_1017': {('t_1019', 'hd/obj1')},
        't_1019': {('t_1018', 'hd/mod')}
    }


def test_filter_2nd_node(deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    assert deep_tree.filter_headdep_dict(
        deep_tree.head2deps,
        lambda t: t != 't_1017'
    ) == {
        't_1016': {('t_1019', 'hd/obj1')},
        't_1019': {('t_1018', 'hd/mod')}
    }


def test_filter_3rd_node(deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    assert deep_tree.filter_headdep_dict(
        deep_tree.head2deps,
        lambda t: t != 't_1019'
    ) == {
        't_1016': {('t_1017', 'hd/mod')},
        't_1017': {('t_1018', 'hd/mod')}
    }


def test_filter_4th_node(deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    assert deep_tree.filter_headdep_dict(
        deep_tree.head2deps,
        lambda t: t != 't_1018'
    ) == {
        't_1016': {('t_1017', 'hd/mod')},
        't_1017': {('t_1019', 'hd/obj1')},
    }


def test_filter_two_nodes(deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    assert deep_tree.filter_headdep_dict(
        deep_tree.head2deps,
        lambda t: t == 't_1016' or t == 't_1018'
    ) == {
        't_1016': {('t_1018', 'hd/mod')}
    }


def test_filter_all_but_two_nodes(very_deep_tree, caplog):
    caplog.set_level(logging.DEBUG)
    head2deps = very_deep_tree.head2deps
    root = min(head2deps)
    leaf = max(head2deps) + 1
    assert ConstituencyTree.filter_headdep_dict(
        head2deps,
        lambda t: t == root or t == leaf
    ) == {root: {(leaf, None)}}


def test_direct_dependents(example_constituency_tree):
    assert example_constituency_tree.get_direct_dependents('asdfas') is None
    assert example_constituency_tree.get_direct_dependents('t_0') is None
    assert example_constituency_tree.get_direct_dependents('t_2') is None
    assert example_constituency_tree.get_direct_dependents('t_1') == {
        't_0',
        't_2'
    }
