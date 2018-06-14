import logging

from multisieve_coreference.constituency_tree import ConstituencyTree


def test_no_filter(naf_object, caplog):
    caplog.set_level(logging.DEBUG)
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    tree = ConstituencyTree(naf_object)
    assert tree.head2deps == {'t_1': {('t_0', 'hd/su'), ('t_2', 'hd/obj1')}}
    assert tree.dep2heads == {
        't_0': {('t_1', 'hd/su')},
        't_2': {('t_1', 'hd/obj1')}
    }
    assert tree.get_constituent('t_1') == {'t_0', 't_1', 't_2'}
    assert tree.get_constituent('t_0') == {'t_0'}
    assert tree.get_constituent('t_2') == {'t_2'}
    assert tree.get_constituent('very random') == {'very random'}


# def test_punct_filter(naf_object):
#     def filt(naf, t):
#         return naf.get_term(t).get_pos() != 'punct'
