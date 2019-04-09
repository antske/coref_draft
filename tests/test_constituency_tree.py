import pytest
import logging

from multisieve_coreference.constituency_tree import ConstituencyTrees


@pytest.fixture
def example_constituency_tree(example_naf_object):
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    return ConstituencyTrees.from_naf(example_naf_object)


@pytest.fixture
def sonar_constituency_tree1(sonar_naf_object1):
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    return ConstituencyTrees.from_naf(sonar_naf_object1)


@pytest.fixture
def sonar_constituency_tree2(sonar_naf_object2):
    return ConstituencyTrees.from_naf(sonar_naf_object2)


@pytest.fixture
def sonar_constituency_tree3(sonar_naf_object3):
    return ConstituencyTrees.from_naf(sonar_naf_object3)


@pytest.fixture
def deep_tree():
    return ConstituencyTrees({
        't_1016': {('t_1017', 'hd/mod')},
        't_1017': {('t_1019', 'hd/obj1')},
        't_1019': {('t_1018', 'hd/mod')}
    })


@pytest.fixture
def not_a_tree():
    # From WR-P-E-C-0000000021.naf
    # <wf id="w2082" offset="11950" length="1" sent="124" para="1">-</wf>
    # <wf id="w2083" offset="11952" length="13" sent="124" para="1">
    #     Signalementen</wf>
    # <wf id="w2084" offset="11966" length="1" sent="124" para="1">:</wf>
    # <wf id="w2085" offset="11968" length="2" sent="124" para="1">..</wf>

    # <!--- / -( - , Signalementen)-->
    # <dep from="t_2081" to="t_2082" rfunc="-- / --" />
    # <!--- / -( - , :)-->
    # <dep from="t_2081" to="t_2083" rfunc="-- / --" />
    # <!--- / -( - , ..)-->
    # <dep from="t_2081" to="t_2084" rfunc="-- / --" />
    # <!--- / -(Signalementen,  - )-->
    # <dep from="t_2082" to="t_2081" rfunc="-- / --" />
    # <!--- / -(Signalementen, :)-->
    # <dep from="t_2082" to="t_2083" rfunc="-- / --" />
    # <!--- / -(Signalementen, ..)-->
    # <dep from="t_2082" to="t_2084" rfunc="-- / --" />
    # <!--- / -(:,  - )-->
    # <dep from="t_2083" to="t_2081" rfunc="-- / --" />
    # <!--- / -(:, Signalementen)-->
    # <dep from="t_2083" to="t_2082" rfunc="-- / --" />
    # <!--- / -(:, ..)-->
    # <dep from="t_2083" to="t_2084" rfunc="-- / --" />
    # <!--- / -(..,  - )-->
    # <dep from="t_2084" to="t_2081" rfunc="-- / --" />
    # <!--- / -(.., Signalementen)-->
    # <dep from="t_2084" to="t_2082" rfunc="-- / --" />
    # <!--- / -(.., :)-->
    # <dep from="t_2084" to="t_2083" rfunc="-- / --" />
    return ConstituencyTrees({
        't_2081': {
            ('t_2082', '-- / --'),
            ('t_2083', '-- / --'),
            ('t_2084', '-- / --'),
        },
        't_2082': {
            ('t_2081', '-- / --'),
            ('t_2083', '-- / --'),
            ('t_2084', '-- / --'),
        },
        't_2083': {
            ('t_2081', '-- / --'),
            ('t_2082', '-- / --'),
            ('t_2084', '-- / --'),
        },
        't_2084': {
            ('t_2081', '-- / --'),
            ('t_2082', '-- / --'),
            ('t_2083', '-- / --'),
        },
    })


@pytest.fixture(params=[10, 100, 1000, 10000])
def very_deep_tree(request):
    return ConstituencyTrees({
        i: {(i + 1, None)} for i in range(request.param)
    })


@pytest.fixture(params=[
    'example_constituency_tree',
    'sonar_constituency_tree1',
    'sonar_constituency_tree2',
    'sonar_constituency_tree3',
    'deep_tree',
    'not_a_tree',
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
    assert any_tree == eval(repr(any_tree))


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
    assert ConstituencyTrees.filter_headdep_dict(
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


def test_filter_not_a_tree(not_a_tree):
    global cycle_count
    cycle_count = 0

    def my_filter(head):
        global cycle_count
        if cycle_count < 1000:
            cycle_count += 1
        else:
            raise AssertionError("This code is in an infinite loop!")
        return head == 't_2082'

    assert ConstituencyTrees.filter_headdep_dict(
        not_a_tree.head2deps,
        my_filter
    ) == {'t_2082': {('t_2082', '-- / --')}}


def test_filter_direct_self_reference_interesting(not_a_tree):
    for key in not_a_tree.head2deps:
        possibly_self_referent = ConstituencyTrees.filter_headdep_dict(
            not_a_tree.head2deps,
            lambda t: t == key
        )
        assert len(
            ConstituencyTrees.filter_direct_self_reference(
                possibly_self_referent
            )
        ) == 0


def test_filter_direct_self_reference_twice(any_tree):
    filtered = ConstituencyTrees.filter_direct_self_reference(
        any_tree.head2deps)
    assert filtered == ConstituencyTrees.filter_direct_self_reference(filtered)
