from ctrader.ml.purged_cv import PurgedKFold


def test_purged_cv_splits():
    cv = PurgedKFold(n_splits=4, embargo_pct=0.05, label_horizon=5)
    splits = list(cv.split(100))
    assert len(splits) == 4
    for tr, te in splits:
        assert len(set(tr).intersection(set(te))) == 0
