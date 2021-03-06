# -*- coding: utf-8 -*-
"""
@brief      test log(time=2s)

"""
import os
import unittest
import copy
from ensae_teaching_cs.homeblog.table_formula import TableFormula


class TestTableFormula_td9(unittest.TestCase):

    def test_td9_json(self):
        fold = os.path.split(__file__)[0]
        data = os.path.join(fold, "data", "td9_by_hours.txt")
        tbl = TableFormula(data)
        tbl = tbl.values_to_float(True)
        jso = []
        for row in tbl:
            r = copy.copy(row)
            r["name"] = r["last_update"]
            jso.append(r)

        assert len(jso) > 0
        outf = os.path.join(fold, "out_json_paris_velib.json")
        if os.path.exists(outf):
            os.remove(outf)
        with open(outf, "w") as f:
            f.write("[\n")
            f.write("\n".join([str(_) for _ in jso]))
            f.write("\n]\n")
        assert os.path.exists(outf)


if __name__ == "__main__":
    unittest.main()
