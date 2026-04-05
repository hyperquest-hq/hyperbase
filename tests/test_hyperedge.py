import unittest

from hyperbase.hyperedge import build_atom, hedge, split_edge_str, str_to_atom


class TestHyperedge(unittest.TestCase):
    def test_hedge1(self):
        assert str(hedge("(is hyperbase/1 great/1)")) == "(is hyperbase/1 great/1)"

    def test_hedge2(self):
        assert (
            str(hedge("(src hyperbase/1 (is hyperbase/1 great/1))"))
            == "(src hyperbase/1 (is hyperbase/1 great/1))"
        )

    def test_hedge3(self):
        assert (
            str(hedge("((is my) brain/1 (super great/1))"))
            == "((is my) brain/1 (super great/1))"
        )

    def test_hedge4(self):
        assert hedge(".") == (".",)

    def test_hedge5(self):
        assert str(hedge("(VAR/C)")) == "(VAR/C)"

    def test_hedge6(self):
        assert (
            str(hedge("((is my) (brain/1) (super great/1))"))
            == "((is my) (brain/1) (super great/1))"
        )

    def test_atom1(self):
        assert hedge("a").atom

    def test_atom2(self):
        assert hedge("hyperbase/C").atom

    def test_atom3(self):
        assert hedge("hyperbase/Cn.p/1").atom

    def test_atom4(self):
        assert hedge("(X/C)").atom

    def test_atom5(self):
        assert not hedge("(is/Pd.sc hyperbase/Cp.s great/C)").atom

    def test_atom_parts1(self):
        assert hedge("hyperbase/C").parts() == ["hyperbase", "C"]

    def test_atom_parts2(self):
        assert hedge("hyperbase").parts() == ["hyperbase"]

    def test_atom_parts3(self):
        assert hedge("go/P.so/1").parts() == ["go", "P.so", "1"]

    def test_atom_parts4(self):
        assert hedge("(X/P.so/1)").parts() == ["X", "P.so", "1"]

    def test_root1(self):
        assert hedge("hyperbase/C").root() == "hyperbase"

    def test_root2(self):
        assert hedge("go/P.so/1").root() == "go"

    def test_build_atom1(self):
        assert build_atom("hyperbase", "C") == hedge("hyperbase/C")

    def test_build_atom2(self):
        assert build_atom("go", "P.so", "1") == hedge("go/P.so/1")

    def test_replace_atom_part1(self):
        assert hedge("hyperbase/C").replace_atom_part(0, "x") == hedge("x/C")

    def test_replace_atom_part2(self):
        assert hedge("xxx/1/yyy").replace_atom_part(1, "77") == hedge("xxx/77/yyy")

    def test_replace_atom_part3(self):
        assert hedge("(XXX/1/yyy)").replace_atom_part(1, "77") == hedge("(XXX/77/yyy)")

    def test_str_to_atom1(self):
        assert str_to_atom("abc") == "abc"

    def test_str_to_atom2(self):
        assert str_to_atom("abc%") == "abc%25"

    def test_str_to_atom3(self):
        assert str_to_atom("/abc") == "%2fabc"

    def test_str_to_atom4(self):
        assert str_to_atom("a bc") == "a%20bc"

    def test_str_to_atom5(self):
        assert str_to_atom("ab(c") == "ab%28c"

    def test_str_to_atom6(self):
        assert str_to_atom("abc)") == "abc%29"

    def test_str_to_atom7(self):
        assert str_to_atom(".abc") == "%2eabc"

    def test_str_to_atom8(self):
        assert str_to_atom("a*bc") == "a%2abc"

    def test_str_to_atom9(self):
        assert str_to_atom("ab&c") == "ab%26c"

    def test_str_to_atom10(self):
        assert str_to_atom("abc@") == "abc%40"

    def test_str_to_atom11(self):
        assert str_to_atom("graph brain/(1).") == "graph%20brain%2f%281%29%2e"

    def test_split_edge_str1(self):
        assert split_edge_str("is hyperbase/1 great/1") == (
            "is",
            "hyperbase/1",
            "great/1",
        )

    def test_split_edge_str2(self):
        assert split_edge_str("size hyperbase/1 7") == ("size", "hyperbase/1", "7")

    def test_split_edge_str3(self):
        assert split_edge_str("size hyperbase/1 7.0") == ("size", "hyperbase/1", "7.0")

    def test_split_edge_str4(self):
        assert split_edge_str("size hyperbase/1 -7") == ("size", "hyperbase/1", "-7")

    def test_split_edge_str5(self):
        assert split_edge_str("size hyperbase/1 -7.0") == (
            "size",
            "hyperbase/1",
            "-7.0",
        )

    def test_split_edge_str6(self):
        assert split_edge_str("src hyperbase/1 (is hyperbase/1 great/1)") == (
            "src",
            "hyperbase/1",
            "(is hyperbase/1 great/1)",
        )

    def test_to_str(self):
        assert str(hedge("(is hyperbase/C great/C)")) == "(is hyperbase/C great/C)"
        assert (
            str(hedge("(src hyperbase/C (is hyperbase/C great/C))"))
            == "(src hyperbase/C (is hyperbase/C great/C))"
        )

    def test_label1(self):
        assert hedge("graph%20brain%2f%281%29%2e/Cn.s/.").label() == "graph brain/(1)."

    def test_label2(self):
        assert hedge("(red/M shoes/C)").label() == "red shoes"

    def test_label3(self):
        assert hedge("(of/B capital/C germany/C)").label() == "capital of germany"

    def test_label4(self):
        assert hedge("(+/B/. capital/C germany/C)").label() == "capital germany"

    def test_label5(self):
        assert (
            hedge("(of/B capital/C west/C germany/C)").label()
            == "capital of west germany"
        )

    def test_label6(self):
        assert (
            hedge("(of/B capital/C (and/B belgium/C europe/C))").label()
            == "capital of belgium and europe"
        )

    def test_connector_atom1(self):
        edge = hedge("(is/P.sc hyperbase/1 great/1)")
        assert edge.connector_atom() == hedge("is/P.sc")

    def test_connector_atom2(self):
        edge = hedge("((not/M is/P.sc) hyperbase/1 great/1)")
        assert edge.connector_atom() == hedge("is/P.sc")

    def test_connector_atom3(self):
        edge = hedge("((maybe/M (not/M is/P.sc)) hyperbase/1 great/1)")
        assert edge.connector_atom() == hedge("is/P.sc")

    def test_connector_atom4(self):
        edge = hedge("(((and/J not/M nope/M) is/P.sc) hyperbase/1 great/1)")
        assert edge.connector_atom() == hedge("is/P.sc")

    def test_atoms1(self):
        assert hedge("(is hyperbase/1 great/1)").atoms() == {
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("great/1"),
        }

    def test_atoms2(self):
        assert hedge("(src hyperbase/2 (is hyperbase/1 great/1))").atoms() == {
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("great/1"),
            hedge("src"),
            hedge("hyperbase/2"),
        }

    def test_atoms3(self):
        assert hedge("hyperbase/1").atoms() == {hedge("hyperbase/1")}

    def test_atoms4(self):
        edge = hedge("(the/Md (of/Br mayor/Cc (the/Md city/Cs)))")
        assert edge.atoms() == {
            hedge("the/Md"),
            hedge("of/Br"),
            hedge("mayor/Cc"),
            hedge("city/Cs"),
        }
        assert hedge("(is (X/C) great/1)").atoms() == {
            hedge("is"),
            hedge("(X/C)"),
            hedge("great/1"),
        }

    def test_all_atoms1(self):
        assert hedge("(is hyperbase/1 great/1)").all_atoms() == [
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("great/1"),
        ]

    def test_all_atoms2(self):
        assert hedge("(src hyperbase/2 (is hyperbase/1 great/1))").all_atoms() == [
            hedge("src"),
            hedge("hyperbase/2"),
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("great/1"),
        ]

    def test_all_atoms3(self):
        assert hedge("hyperbase/1").all_atoms() == [hedge("hyperbase/1")]

    def test_all_atoms4(self):
        edge = hedge("(the/Md (of/Br mayor/Cc (the/Md city/Cs)))")
        assert edge.all_atoms() == [
            hedge("the/Md"),
            hedge("of/Br"),
            hedge("mayor/Cc"),
            hedge("the/Md"),
            hedge("city/Cs"),
        ]

    def test_all_atoms5(self):
        edge = hedge("(the/Md (of/Br (X/C) (the/Md city/Cs)))")
        assert edge.all_atoms() == [
            hedge("the/Md"),
            hedge("of/Br"),
            hedge("(X/C)"),
            hedge("the/Md"),
            hedge("city/Cs"),
        ]

    def test_size1(self):
        assert hedge("hyperbase/1").size() == 1

    def test_size2(self):
        assert hedge("(X/C)").size() == 1

    def test_size3(self):
        assert hedge("(is hyperbase/1 great/1)").size() == 3

    def test_size4(self):
        assert hedge("(is hyperbase/1 (super great/1))").size() == 4

    def test_depth1(self):
        assert hedge("hyperbase/1").depth() == 0

    def test_depth2(self):
        assert hedge("(is hyperbase/1 great/1)").depth() == 1

    def test_depth3(self):
        assert hedge("(is hyperbase/1 (super great/1))").depth() == 2

    def test_depth4(self):
        assert hedge("(is hyperbase/1 (super (X/C)))").depth() == 2

    def test_contains(self):
        edge = hedge("(is/Pd.sc piron/C (of/B capital/C piripiri/C))")
        assert edge.contains(hedge("is/Pd.sc"))
        assert edge.contains(hedge("piron/C"))
        assert edge.contains(hedge("(of/B capital/C piripiri/C)"))
        assert edge.contains(hedge("piripiri/C"))
        assert not edge.contains(hedge("1111/C"))

    def test_contains_pares_atom(self):
        edge = hedge("(is/Pd.sc piron/C (of/B capital/C (XYZ)))")
        assert edge.contains(hedge("is/Pd.sc"))
        assert edge.contains(hedge("piron/C"))
        assert edge.contains(hedge("(of/B capital/C (XYZ))"))
        assert edge.contains(hedge("(XYZ)"))
        assert not edge.contains(hedge("1111/C"))

    def test_subedges1(self):
        assert hedge("hyperbase/1").subedges() == {hedge("hyperbase/1")}

    def test_subedges2(self):
        assert hedge("(is hyperbase/1 great/1)").subedges() == {
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("great/1"),
            hedge("(is hyperbase/1 great/1)"),
        }

    def test_subedges3(self):
        assert hedge("(is hyperbase/1 (super great/1))").subedges() == {
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("super"),
            hedge("great/1"),
            hedge("(super great/1)"),
            hedge("(is hyperbase/1 (super great/1))"),
        }

    def test_subedges4(self):
        assert hedge("(is hyperbase/1 (X/C))").subedges() == {
            hedge("is"),
            hedge("hyperbase/1"),
            hedge("(X/C)"),
            hedge("(is hyperbase/1 (X/C))"),
        }

    def test_atom_role(self):
        assert hedge("hyperbase/Cp.s/1").role() == ["Cp", "s"]

    def test_atom_role_implied_conjunction(self):
        assert hedge("and").role() == ["J"]

    def test_atom_simplify_atom1(self):
        assert hedge("hyperbase/Cp/1").simplify() == hedge("hyperbase/C")

    def test_atom_simplify_atom2(self):
        assert hedge("hyperbase").simplify() == hedge("hyperbase")

    def test_atom_simplify_atom3(self):
        assert hedge("say/Pd.sr.|f----/en").simplify() == hedge("say/P.sr")

    def test_atom_simplify_atom4(self):
        assert hedge("say/Pd.sr.|f----/en").simplify(subtypes=True) == hedge(
            "say/Pd.sr"
        )

    def test_atom_simplify_atom5(self):
        assert hedge("say/Pd.sr.|f----/en").simplify(namespaces=True) == hedge(
            "say/P.sr/en"
        )

    def test_atom_simplify_edge(self):
        edge = hedge("is/Pd.sc.|f----/en mary/Cp.s/en nice/Ca/en")
        assert edge.simplify() == hedge("is/P.sc mary/C nice/C")
        assert edge.simplify(subtypes=True) == hedge("is/Pd.sc mary/Cp nice/Ca")
        assert edge.simplify(namespaces=True) == hedge("is/P.sc/en mary/C/en nice/C/en")
        assert edge.simplify(subtypes=True, namespaces=True) == hedge(
            "is/Pd.sc/en mary/Cp/en nice/Ca/en"
        )

    def test_atom_type(self):
        assert hedge("hyperbase/Cp.s/1").type() == "Cp"

    def test_atom_mtype(self):
        assert hedge("hyperbase/Cp.s/1").mtype() == "C"

    def test_atom_type_implied_conjunction(self):
        assert hedge("and").type() == "J"

    def test_non_atom_type1(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").type() == "Rd"

    def test_non_atom_type2(self):
        assert hedge("(red/M shoes/Cc.p)").type() == "Cc"

    def test_non_atom_type3(self):
        assert hedge("(before/Tt noon/C)").type() == "St"

    def test_non_atom_type4(self):
        assert hedge("(very/M large/M)").type() == "M"

    def test_non_atom_type5(self):
        assert hedge("((very/M large/M) shoes/Cc.p)").type() == "Cc"

    def test_non_atom_type6(self):
        assert hedge("(will/M be/Pd.sc)").type() == "Pd"

    def test_non_atom_type7(self):
        assert hedge("((will/M be/Pd.sc) john/Cp.s rich/C)").type() == "Rd"

    def test_non_atom_type8(self):
        assert hedge("(play/T piano/Cc.s)").type() == "S"

    def test_non_atom_type9(self):
        assert hedge("(and/J meat/Cc.s potatoes/Cc.p)").type() == "C"

    def test_non_atom_type10(self):
        assert hedge("(and/J (is/Pd.so hyperbase/Cp.s great/C))").type() == "R"

    def test_non_atom_mtype1(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").type() == "Rd"

    def test_non_atom_mtype2(self):
        assert hedge("(red/M shoes/Cc.p)").mtype() == "C"

    def test_non_atom_mtype3(self):
        assert hedge("(before/Tt noon/C)").mtype() == "S"

    def test_non_atom_mtype4(self):
        assert hedge("(very/M large/M)").mtype() == "M"

    def test_non_atom_mtype5(self):
        assert hedge("((very/M large/M) shoes/Cc.p)").mtype() == "C"

    def test_non_atom_mtype6(self):
        assert hedge("(will/M be/Pd.sc)").mtype() == "P"

    def test_non_atom_mtype7(self):
        assert hedge("((will/M be/Pd.sc) john/Cp.s rich/C)").mtype() == "R"

    def test_non_atom_mtype8(self):
        assert hedge("(play/T piano/Cc.s)").mtype() == "S"

    def test_non_atom_mtype9(self):
        assert hedge("(and/J meat/Cc.s potatoes/Cc.p)").mtype() == "C"

    def test_non_atom_mtype10(self):
        assert hedge("(and/J (is/Pd.so hyperbase/Cp.s great/C))").mtype() == "R"

    def test_connector_type1(self):
        assert hedge("hyperbase/Cp.s/1").connector_type() is None

    def test_connector_type2(self):
        assert hedge("hyperbase").connector_type() is None

    def test_connector_type3(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").connector_type() == "Pd"

    def test_connector_type4(self):
        assert hedge("(red/M shoes/Cn.p)").connector_type() == "M"

    def test_connector_type5(self):
        assert hedge("(before/Tt noon/C)").connector_type() == "Tt"

    def test_connector_type6(self):
        assert hedge("(very/M large/M)").connector_type() == "M"

    def test_connector_type7(self):
        assert hedge("((very/M large/M) shoes/Cn.p)").connector_type() == "M"

    def test_connector_type8(self):
        assert hedge("(will/M be/Pd.sc)").connector_type() == "M"

    def test_connector_type9(self):
        assert hedge("((will/M be/Pd.sc) john/Cp.s rich/C)").connector_type() == "Pd"

    def test_connector_type10(self):
        assert hedge("(play/T piano/Cn.s)").connector_type() == "T"

    def test_connector_mtype1(self):
        assert hedge("hyperbase/Cp.s/1").connector_mtype() is None

    def test_connector_mtype2(self):
        assert hedge("hyperbase").connector_mtype() is None

    def test_connector_mtype3(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").connector_mtype() == "P"

    def test_connector_mtype4(self):
        assert hedge("(red/M shoes/Cn.p)").connector_mtype() == "M"

    def test_connector_mtype5(self):
        assert hedge("(before/Tt noon/C)").connector_mtype() == "T"

    def test_connector_mtype6(self):
        assert hedge("(very/M large/M)").connector_mtype() == "M"

    def test_connector_mtype7(self):
        assert hedge("((very/M large/M) shoes/Cn.p)").connector_mtype() == "M"

    def test_connector_mtype8(self):
        assert hedge("(will/M be/Pd.sc)").connector_mtype() == "M"

    def test_connector_mtype9(self):
        assert hedge("((will/M be/Pd.sc) john/Cp.s rich/C)").connector_mtype() == "P"

    def test_connector_mtype10(self):
        assert hedge("(play/T piano/Cn.s)").connector_mtype() == "T"

    def test_t1(self):
        assert hedge("hyperbase/Cp.s/1").t == "Cp"

    def test_t2(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").t == "Rd"

    def test_t3(self):
        assert hedge("(very/M large/M)").t == "M"

    def test_mt1(self):
        assert hedge("hyperbase/Cp.s/1").mt == "C"

    def test_mt2(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").mt == "R"

    def test_mt3(self):
        assert hedge("(very/M large/M)").mt == "M"

    def test_ct1(self):
        assert hedge("hyperbase/Cp.s/1").ct is None

    def test_ct2(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").ct == "Pd"

    def test_ct3(self):
        assert hedge("(red/M shoes/Cn.p)").ct == "M"

    def test_cmt1(self):
        assert hedge("hyperbase/Cp.s/1").cmt is None

    def test_cmt2(self):
        assert hedge("(is/Pd.so hyperbase/Cp.s great/C)").cmt == "P"

    def test_cmt3(self):
        assert hedge("(red/M shoes/Cn.p)").cmt == "M"

    def test_atom_with_type1(self):
        assert hedge("(+/B a/Cn b/Cp)").atom_with_type("C") == hedge("a/Cn")

    def test_atom_with_type2(self):
        assert hedge("(+/B a/C b/Cp)").atom_with_type("Cp") == hedge("b/Cp")

    def test_atom_with_type3(self):
        assert hedge("(+/B a/C b/Cp)").atom_with_type("P") is None

    def test_atom_with_type4(self):
        assert hedge("a/Cn").atom_with_type("C") == hedge("a/Cn")

    def test_atom_with_type5(self):
        assert hedge("a/Cn").atom_with_type("Cn") == hedge("a/Cn")

    def test_atom_with_type6(self):
        assert hedge("a/Cn").atom_with_type("Cp") is None

    def test_atom_with_type7(self):
        assert hedge("a/Cn").atom_with_type("P") is None

    def test_argroles_connector_atom1(self):
        edge = hedge("s/Bp.am")
        assert edge.argroles() == "am"

    def test_argroles_connector_atom2(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert edge.argroles() == "sx"

    def test_argroles_connector_atom3(self):
        edge = hedge("come/Pd")
        assert edge.argroles() == ""

    def test_argroles_connector_atom4(self):
        edge = hedge("red/M")
        assert edge.argroles() == ""

    def test_argroles_connector_atom5(self):
        edge = hedge("berlin/Cp.s/de")
        assert edge.argroles() == ""

    def test_argroles_connector_edge1(self):
        edge = hedge("(is/Mv.|f--3s/en influenced/Pd.xpa.<pf---/en)")
        assert edge.argroles() == "xpa"

    def test_argroles_connector_edge2(self):
        edge = hedge("(is/Mv.|f--3s/en influenced/Pd)")
        assert edge.argroles() == ""

    def test_argroles_edge1(self):
        edge = hedge("((not/M is/P.sc) bob/C sad/C)")
        assert edge.argroles() == "sc"

    def test_argroles_edge2(self):
        edge = hedge("(of/B.ma city/C berlin/C)")
        assert edge.argroles() == "ma"

    def test_argroles_edge3(self):
        edge = hedge("(of/B city/C berlin/C)")
        assert edge.argroles() == ""

    def test_replace_argroles_atom1(self):
        edge = hedge("s/Bp.am")
        assert str(edge.replace_argroles("ma")) == "s/Bp.ma"

    def test_replace_argroles_atom2(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert str(edge.replace_argroles("scx")) == "come/Pd.scx.-i----/en"

    def test_replace_argroles_atom3(self):
        edge = hedge("come/Pd/en")
        assert str(edge.replace_argroles("scx")) == "come/Pd.scx/en"

    def test_replace_argroles_atom4(self):
        edge = hedge("xxx")
        assert str(edge.replace_argroles("scx")) == "xxx"

    def test__insert_argrole_atom1(self):
        edge = hedge("s/Bp.am")
        assert str(edge._insert_argrole("m", 0)) == "s/Bp.mam"

    def test__insert_argrole_atom2(self):
        edge = hedge("s/Bp.am")
        assert str(edge._insert_argrole("m", 1)) == "s/Bp.amm"

    def test__insert_argrole_atom3(self):
        edge = hedge("s/Bp.am")
        assert str(edge._insert_argrole("m", 2)) == "s/Bp.amm"

    def test__insert_argrole_atom4(self):
        edge = hedge("s/Bp.am")
        assert str(edge._insert_argrole("m", 3)) == "s/Bp.amm"

    def test__insert_argrole_atom5(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert str(edge._insert_argrole("x", 0)) == "come/Pd.xsx.-i----/en"

    def test__insert_argrole_atom6(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert str(edge._insert_argrole("x", 1)) == "come/Pd.sxx.-i----/en"

    def test__insert_argrole_atom7(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert str(edge._insert_argrole("x", 2)) == "come/Pd.sxx.-i----/en"

    def test__insert_argrole_atom8(self):
        edge = hedge("come/Pd.sx.-i----/en")
        assert str(edge._insert_argrole("x", 100)) == "come/Pd.sxx.-i----/en"

    def test__insert_argrole_atom9(self):
        edge = hedge("come/Pd/en")
        assert str(edge._insert_argrole("s", 0)) == "come/Pd.s/en"

    def test__insert_argrole_atom10(self):
        edge = hedge("come/Pd/en")
        assert str(edge._insert_argrole("s", 1)) == "come/Pd.s/en"

    def test__insert_argrole_atom11(self):
        edge = hedge("come/Pd/en")
        assert str(edge._insert_argrole("s", 100)) == "come/Pd.s/en"

    def test__insert_argrole_atom12(self):
        edge = hedge("xxx")
        assert str(edge._insert_argrole("s", 0)) == "xxx"

    def test__insert_argrole_atom13(self):
        edge = hedge("xxx")
        assert str(edge._insert_argrole("s", 1)) == "xxx"

    def test__insert_argrole_atom14(self):
        edge = hedge("xxx")
        assert str(edge._insert_argrole("s", 100)) == "xxx"

    def test_replace_argroles_edge1(self):
        edge = hedge("(s/Bp.am x/C y/C)")
        assert str(edge.replace_argroles("ma")) == "(s/Bp.ma x/C y/C)"

    def test_replace_argroles_edge2(self):
        edge = hedge("((m/M s/Bp.am) x/C y/C)")
        assert str(edge.replace_argroles("ma")) == "((m/M s/Bp.ma) x/C y/C)"

    def test_replace_argroles_edge3(self):
        edge = hedge("(come/Pd.sx.-i----/en you/C here/C)")
        assert (
            str(edge.replace_argroles("scx")) == "(come/Pd.scx.-i----/en you/C here/C)"
        )

    def test_replace_argroles_edge4(self):
        edge = hedge("(come/Pd/en you/C here/C)")
        assert str(edge.replace_argroles("scx")) == "(come/Pd.scx/en you/C here/C)"

    def test_replace_argroles_edge5(self):
        edge = hedge("((do/M come/Pd/en) you/C here/C)")
        assert (
            str(edge.replace_argroles("scx")) == "((do/M come/Pd.scx/en) you/C here/C)"
        )

    def test_replace_argroles_edge6(self):
        edge = hedge("(come you/C here/C)")
        assert str(edge.replace_argroles("scx")) == "(come you/C here/C)"

    def test__insert_argrole_edge1(self):
        edge = hedge("(s/Bp.am x/C y/C)")
        assert str(edge._insert_argrole("m", 0)) == "(s/Bp.mam x/C y/C)"

    def test__insert_argrole_edge2(self):
        edge = hedge("(s/Bp.am x/C y/C)")
        assert str(edge._insert_argrole("m", 1)) == "(s/Bp.amm x/C y/C)"

    def test__insert_argrole_edge3(self):
        edge = hedge("(s/Bp.am x/C y/C)")
        assert str(edge._insert_argrole("m", 2)) == "(s/Bp.amm x/C y/C)"

    def test__insert_argrole_edge4(self):
        edge = hedge("(s/Bp.am x/C y/C)")
        assert str(edge._insert_argrole("m", 3)) == "(s/Bp.amm x/C y/C)"

    def test__insert_argrole_edge5(self):
        edge = hedge("((m/M s/Bp.am) x/C y/C)")
        assert str(edge._insert_argrole("m", 0)) == "((m/M s/Bp.mam) x/C y/C)"

    def test__insert_argrole_edge6(self):
        edge = hedge("(come/Pd.sx.-i----/en you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 0)) == "(come/Pd.xsx.-i----/en you/C here/C)"
        )

    def test__insert_argrole_edge7(self):
        edge = hedge("(come/Pd.sx.-i----/en you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 1)) == "(come/Pd.sxx.-i----/en you/C here/C)"
        )

    def test__insert_argrole_edge8(self):
        edge = hedge("(come/Pd.sx.-i----/en you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 2)) == "(come/Pd.sxx.-i----/en you/C here/C)"
        )

    def test__insert_argrole_edge9(self):
        edge = hedge("(come/Pd.sx.-i----/en you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 100))
            == "(come/Pd.sxx.-i----/en you/C here/C)"
        )

    def test__insert_argrole_edge10(self):
        edge = hedge("(come/Pd/en you/C here/C)")
        assert str(edge._insert_argrole("s", 0)) == "(come/Pd.s/en you/C here/C)"

    def test__insert_argrole_edge11(self):
        edge = hedge("(come/Pd/en you/C here/C)")
        assert str(edge._insert_argrole("s", 1)) == "(come/Pd.s/en you/C here/C)"

    def test__insert_argrole_edge12(self):
        edge = hedge("(come/Pd/en you/C here/C)")
        assert str(edge._insert_argrole("s", 100)) == "(come/Pd.s/en you/C here/C)"

    def test__insert_argrole_edge13(self):
        edge = hedge("(come you/C here/C)")
        assert str(edge._insert_argrole("s", 0)) == "(come you/C here/C)"

    def test__insert_argrole_edge14(self):
        edge = hedge("(come you/C here/C)")
        assert str(edge._insert_argrole("s", 1)) == "(come you/C here/C)"

    def test__insert_argrole_edge15(self):
        edge = hedge("(come you/C here/C)")
        assert str(edge._insert_argrole("s", 100)) == "(come you/C here/C)"

    def test__insert_argrole_edge16(self):
        edge = hedge("((do/M come/Pd.sx.-i----/en) you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 2))
            == "((do/M come/Pd.sxx.-i----/en) you/C here/C)"
        )

    def test_add_argument1(self):
        edge = hedge("(is/Pd.sc/en sky/C blue/C)")
        assert edge.add_argument(hedge("today/C"), "x", 0) == hedge(
            "(is/Pd.xsc/en today/C sky/C blue/C)"
        )
        assert edge.add_argument(hedge("today/C"), "x", 1) == hedge(
            "(is/Pd.sxc/en sky/C today/C blue/C)"
        )
        assert edge.add_argument(hedge("today/C"), "x", 2) == hedge(
            "(is/Pd.scx/en sky/C blue/C today/C)"
        )
        assert edge.add_argument(hedge("today/C"), "x", 100) == hedge(
            "(is/Pd.scx/en sky/C blue/C today/C)"
        )

    def test_add_argument2(self):
        edge = hedge("((not/M is/Pd.sc/en) sky/C blue/C)")
        assert edge.add_argument(hedge("today/C"), "x", 1) == hedge(
            "((not/M is/Pd.sxc/en) sky/C today/C blue/C)"
        )

    def test_add_argument3(self):
        edge = hedge("((m/M b/B.am) x/C y/C)")
        assert edge.add_argument(hedge("z/C"), "a", 2) == hedge(
            "((m/M b/B.ama) x/C y/C z/C)"
        )

    def test_add_argument_no_pos1(self):
        edge = hedge("(is/Pd.sc/en sky/C blue/C)")
        assert edge.add_argument(hedge("today/C"), "x") == hedge(
            "(is/Pd.scx/en sky/C blue/C today/C)"
        )

    def test_add_argument_no_pos2(self):
        edge = hedge("((not/M is/Pd.sc/en) sky/C blue/C)")
        assert edge.add_argument(hedge("today/C"), "x") == hedge(
            "((not/M is/Pd.scx/en) sky/C blue/C today/C)"
        )

    def test_add_argument_no_pos3(self):
        edge = hedge("((m/M b/B.am) x/C y/C)")
        assert edge.add_argument(hedge("z/C"), "a") == hedge(
            "((m/M b/B.ama) x/C y/C z/C)"
        )

    def test_replace_argroles_var1(self):
        edge = hedge("((var s/Bp.am V) x/C y/C)")
        assert str(edge.replace_argroles("ma")) == "((var s/Bp.ma V) x/C y/C)"

    def test_replace_argroles_var2(self):
        edge = hedge("((var (m/M s/Bp.am) V) x/C y/C)")
        assert str(edge.replace_argroles("ma")) == "((var (m/M s/Bp.ma) V) x/C y/C)"

    def test_replace_argroles_var3(self):
        edge = hedge("((var come/Pd.sx.-i----/en V) you/C here/C)")
        assert (
            str(edge.replace_argroles("scx"))
            == "((var come/Pd.scx.-i----/en V) you/C here/C)"
        )

    def test_replace_argroles_var4(self):
        edge = hedge("((var come/Pd/en V) you/C here/C)")
        assert (
            str(edge.replace_argroles("scx")) == "((var come/Pd.scx/en V) you/C here/C)"
        )

    def test_replace_argroles_var5(self):
        edge = hedge("((var (do/M come/Pd/en) V) you/C here/C)")
        assert (
            str(edge.replace_argroles("scx"))
            == "((var (do/M come/Pd.scx/en) V) you/C here/C)"
        )

    def test_replace_argroles_var6(self):
        edge = hedge("((var come V) you/C here/C)")
        assert str(edge.replace_argroles("scx")) == "((var come V) you/C here/C)"

    def test__insert_argrole_var1(self):
        edge = hedge("((var s/Bp.am V) x/C y/C)")
        assert str(edge._insert_argrole("m", 0)) == "((var s/Bp.mam V) x/C y/C)"

    def test__insert_argrole_var2(self):
        edge = hedge("((var come/Pd.sx.-i----/en V) you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 1))
            == "((var come/Pd.sxx.-i----/en V) you/C here/C)"
        )

    def test__insert_argrole_var3(self):
        edge = hedge("((var come/Pd/en V) you/C here/C)")
        assert (
            str(edge._insert_argrole("s", 100)) == "((var come/Pd.s/en V) you/C here/C)"
        )

    def test__insert_argrole_var4(self):
        edge = hedge("((var (do/M come/Pd.sx.-i----/en) V) you/C here/C)")
        assert (
            str(edge._insert_argrole("x", 2))
            == "((var (do/M come/Pd.sxx.-i----/en) V) you/C here/C)"
        )

    def test_insert_edge_with_var1(self):
        edge = hedge("((var is/Pd.sc/en V) sky/C blue/C)")
        assert edge.add_argument(hedge("today/C"), "x", 0) == hedge(
            "((var is/Pd.xsc/en V) today/C sky/C blue/C)"
        )

    def test_insert_edge_with_var2(self):
        edge = hedge("((var (m/M b/B.am) V) x/C y/C)")
        assert edge.add_argument(hedge("z/C"), "a", 2) == hedge(
            "((var (m/M b/B.ama) V) x/C y/C z/C)"
        )

    def test_arguments_with_role(self):
        edge_str = (
            "((have/Mv.|f----/en (been/Mv.<pf---/en tracking/Pd.sox.|pg---/en)) (from/Br.ma/en "
            "satellites/Cc.p/en (and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en))) "
            "(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en) (since/Tt/en 1979/C#/en))"
        )
        edge = hedge(edge_str)

        subj = hedge(
            "(from/Br.ma/en satellites/Cc.p/en (and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en)))"
        )
        obj = hedge("(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en)")
        spec = hedge("(since/Tt/en 1979/C#/en)")

        assert edge.arguments_with_role("s") == [subj]
        assert edge.arguments_with_role("o") == [obj]
        assert edge.arguments_with_role("x") == [spec]
        assert edge.arguments_with_role("p") == []

    def test_arguments_with_role_no_roles(self):
        edge_str = (
            "((have/Mv.|f----/en (been/Mv.<pf---/en tracking/Pd)) (from/Br.ma/en satellites/Cc.p/en "
            "(and/B+/en nasa/Cp.s/en (other/Ma/en agencies/Cc.p/en))) "
            "(+/B.aam/. sea/Cc.s/en ice/Cc.s/en changes/Cc.p/en) (since/Tt/en 1979/C#/en))"
        )
        edge = hedge(edge_str)

        assert edge.arguments_with_role("s") == []
        assert edge.arguments_with_role("o") == []
        assert edge.arguments_with_role("x") == []
        assert edge.arguments_with_role("p") == []

    def test_arguments_with_role_atom(self):
        edge = hedge("tracking/Pd.sox.|pg---/en")

        assert edge.arguments_with_role("s") == []
        assert edge.arguments_with_role("o") == []
        assert edge.arguments_with_role("x") == []
        assert edge.arguments_with_role("p") == []

    def test_check_correctness_ok1(self):
        edge = hedge("(red/M shoes/C)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok2(self):
        edge = hedge("(+/B.am john/C smith/C)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok3(self):
        edge = hedge("(in/T 1976/C)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok4(self):
        edge = hedge("(happened/P.sxx it/C before/C (in/T 1976/C))")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok5(self):
        edge = hedge("(and/J red/C green/C blue/C)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok6(self):
        edge = hedge("(likes/P.sc x/C y/C)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_ok7(self):
        edge = hedge("(not/M likes/P.sc)")
        output = edge.check_correctness()
        assert output == {}

    def test_check_correctness_wrong1(self):
        edge = hedge("x/G")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong2(self):
        edge = hedge("(of/C capital/C mars/C)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong3(self):
        edge = hedge("(+/B john/C smith/C iii/C)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong4(self):
        edge = hedge("(of/B capital/C red/M)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong5(self):
        edge = hedge("(in/T 1976/C 1977/C)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong6(self):
        edge = hedge("(in/T red/M)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong7(self):
        edge = hedge("(is/P red/M)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong8(self):
        edge = hedge("(and/J one/C)")
        output = edge.check_correctness()
        assert edge in output

    def test_check_correctness_wrong_deep1(self):
        edge = hedge("(:/J x/C x/G)")
        output = edge.check_correctness()
        assert hedge("x/G") in output

    def test_check_correctness_wrong_deep2(self):
        edge = hedge("(:/J x/C (of/C capital/C mars/C))")
        output = edge.check_correctness()
        assert hedge("(of/C capital/C mars/C)") in output

    def test_check_correctness_wrong_deep3(self):
        edge = hedge("(:/J x/C (+/B john/C smith/C iii/C))")
        output = edge.check_correctness()
        assert hedge("(+/B john/C smith/C iii/C)") in output

    def test_check_correctness_wrong_deep4(self):
        edge = hedge("(:/J x/C (of/B capital/C red/M))")
        output = edge.check_correctness()
        assert hedge("(of/B capital/C red/M)") in output

    def test_check_correctness_wrong_deep5(self):
        edge = hedge("(:/J x/C (in/T 1976/C 1977/C))")
        output = edge.check_correctness()
        assert hedge("(in/T 1976/C 1977/C)") in output

    def test_check_correctness_wrong_deep6(self):
        edge = hedge("(:/J x/C (in/T red/M))")
        output = edge.check_correctness()
        assert hedge("(in/T red/M)") in output

    def test_check_correctness_wrong_deep7(self):
        edge = hedge("(:/J x/C (is/P red/M))")
        output = edge.check_correctness()
        assert hedge("(is/P red/M)") in output

    def test_check_correctness_wrong_deep8(self):
        edge = hedge("(:/J x/C (and/J one/C))")
        output = edge.check_correctness()
        assert hedge("(and/J one/C)") in output

    def test_check_correctness_wrong_argroles1(self):
        edge = hedge("(likes/P.ss x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/P.ss x/C y/C)") in output

    def test_check_correctness_wrong_argroles2(self):
        edge = hedge("(likes/P.cc x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/P.cc x/C y/C)") in output

    def test_check_correctness_wrong_argroles3(self):
        edge = hedge("(likes/P.scx x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/P.scx x/C y/C)") in output

    def test_check_correctness_wrong_argroles4(self):
        edge = hedge("(likes/P.sz x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/P.sz x/C y/C)") in output

    def test_check_correctness_wrong_argroles5(self):
        edge = hedge("(likes/B.sc x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/B.sc x/C y/C)") in output

    def test_check_correctness_wrong_argroles6(self):
        edge = hedge("(likes/P x/C y/C)")
        output = edge.check_correctness()
        assert hedge("(likes/P x/C y/C)") in output

    def test_normalized_1(self):
        edge = hedge("(plays/Pd.os chess/C mary/C)")
        assert edge.normalise() == hedge("(plays/Pd.so mary/C chess/C)")

    def test_normalized_2(self):
        edge = hedge("(plays/Pd chess/C mary/C)")
        assert edge.normalise() == hedge("(plays/Pd chess/C mary/C)")

    def test_normalized_3(self):
        edge = hedge("(plays/Pd.os (of/B.am chess/C games/C) mary/C)")
        assert edge.normalise() == hedge(
            "(plays/Pd.so mary/C (of/B.ma games/C chess/C))"
        )

    def test_normalized_4(self):
        edge = hedge("(plays/Pd.os.xxx/en chess/C mary/C)")
        assert edge.normalise() == hedge("(plays/Pd.so.xxx/en mary/C chess/C)")

    def test_normalized_5(self):
        edge = hedge("plays/Pd.os.xxx/en")
        assert edge.normalise() == hedge("plays/Pd.so.xxx/en")

    def test_normalized_6(self):
        edge = hedge("of/Br.am/en")
        assert edge.normalise() == hedge("of/Br.ma/en")

    def test_normalized_7(self):
        edge = hedge("plays/Pd.{os}.xxx/en")
        assert edge.normalise() == hedge("plays/Pd.{so}.xxx/en")

    def test_bug_fix1(self):
        edge_str = "((ahead/M/en (would/Mm/en go/P..-i-----/en)))"
        edge = hedge(edge_str)
        assert edge_str == str(edge)

    def test_remove_argroles_atom1(self):
        edge = hedge("come/Pd.sx")
        assert str(edge.remove_argroles()) == "come/Pd"

    def test_remove_argroles_atom2(self):
        edge = hedge("come/Pd")
        assert str(edge.remove_argroles()) == "come/Pd"

    def test_replace_argroles_atom_none(self):
        edge = hedge("come/Pd.sx")
        assert str(edge.replace_argroles(None)) == "come/Pd"

    def test_replace_argroles_atom_empty(self):
        edge = hedge("come/Pd.sx")
        assert str(edge.replace_argroles("")) == "come/Pd"

    def test_replace_argroles_edge_none(self):
        edge = hedge("(come/Pd.sx you/C here/C)")
        assert str(edge.replace_argroles(None)) == "(come/Pd you/C here/C)"

    def test_replace_argroles_edge_empty(self):
        edge = hedge("(come/Pd.sx you/C here/C)")
        assert str(edge.replace_argroles("")) == "(come/Pd you/C here/C)"

    def test_replace_argroles_deep_none(self):
        edge = hedge("((not/M is/P.sc) bob/C sad/C)")
        assert str(edge.replace_argroles(None)) == "((not/M is/P) bob/C sad/C)"


if __name__ == "__main__":
    unittest.main()
