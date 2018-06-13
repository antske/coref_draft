import logging

from multisieve_coreference.constituency_tree import ConstituencyTree


def test_no_filter(naf_object, caplog):
    caplog.set_level(logging.DEBUG)
    # <dep from="t_1" to="t_0" rfunc="hd/su" />
    # <!--hd/obj1(herkende, zichzelf)-->
    # <dep from="t_1" to="t_2" rfunc="hd/obj1" />
    tree = ConstituencyTree(naf_object)
    assert len(tree.head2deps) == 1
    assert len(tree.dep2heads) == 2   # t_0 and t_2
    assert len(tree.get_constituent('t_1')) == 3    # all three
    assert len(tree.get_constituent('t_0')) == 1
    assert len(tree.get_constituent('t_2')) == 1
    assert len(tree.get_constituent('very random')) == 1


# def test_punct_filter(naf_object):
#     def filt(naf, t):
#         return naf.get_term(t).get_pos() != 'punct'
