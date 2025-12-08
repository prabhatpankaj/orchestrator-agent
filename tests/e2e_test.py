from executor.execute import execute

def test_basic():
    result = execute("Find python jobs and estimate salary")
    assert len(result) > 0
