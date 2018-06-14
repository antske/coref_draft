import pytest

from multisieve_coreference.constituency_tree import ConstituencyTree


@pytest.fixture
def constituency_tree(naf_object):
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    return ConstituencyTree.from_naf(naf_object)


def test_no_filter(constituency_tree, caplog):
    assert constituency_tree.head2deps == {
        't_1': {
            ('t_0', 'hd/su'),
            ('t_2', 'hd/obj1')
        }
    }
    assert constituency_tree.dep2heads == {
        't_0': {('t_1', 'hd/su')},
        't_2': {('t_1', 'hd/obj1')}
    }
    assert constituency_tree.get_constituent('t_1') == {'t_0', 't_1', 't_2'}
    assert constituency_tree.get_constituent('t_0') == {'t_0'}
    assert constituency_tree.get_constituent('t_2') == {'t_2'}
    assert constituency_tree.get_constituent('very random') == {'very random'}


def test_repr(constituency_tree):
    repr(constituency_tree)


def test_direct_dependents(constituency_tree):
    assert constituency_tree.get_direct_dependents('asdfas') is None
    assert constituency_tree.get_direct_dependents('t_0') is None
    assert constituency_tree.get_direct_dependents('t_2') is None
    assert constituency_tree.get_direct_dependents('t_1') == {'t_0', 't_2'}


# def test_punct_filter(naf_object):
#     def filt(naf, t):
#         return naf.get_term(t).get_pos() != 'punct'
