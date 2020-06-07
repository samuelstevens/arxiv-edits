from arxivedits.util import sliding_window, consecutive_values


def test_default_window():
    initial_list = list(range(3))

    expected_window = [(None, 0, 1), (0, 1, 2), (1, 2, None)]

    assert list(sliding_window(initial_list)) == expected_window


def test_window_with_default():
    initial_list = list(range(3))

    expected_window = [(-1, 0, 1), (0, 1, 2), (1, 2, -1)]

    assert list(sliding_window(initial_list, -1)) == expected_window


def test_window_too_short():
    initial_list = list(range(1))

    expected_window = [(None, 0, None)]

    assert list(sliding_window(initial_list)) == expected_window


def test_window_empty():
    initial_list = []

    expected_window = []

    assert list(sliding_window(initial_list)) == expected_window


def test_window_size_2():
    initial_list = list(range(3))

    expected_window = [
        (None, None, 0, 1, 2),
        (None, 0, 1, 2, None),
        (0, 1, 2, None, None),
    ]

    assert list(sliding_window(initial_list, size=2)) == expected_window


def test_consecutive_values():
    initial_list = [0, 0, 1, 2, 3, 4, 4, 2, 6]

    expected_groups = [[0, 0], [2], [4, 4, 2, 6]]

    comparison_test = lambda x: x % 2 == 0

    actual_groups = consecutive_values(initial_list, comparison_test)

    assert actual_groups == expected_groups


def test_consecutive_values_empty_input():
    initial_list = []

    expected_groups = []

    comparison_test = lambda x: True

    actual_groups = consecutive_values(initial_list, comparison_test)

    assert actual_groups == expected_groups


def test_consecutive_values_end_of_list_true():
    initial_list = [True, False, False, False, True]

    expected_groups = [[True], [True]]

    comparison_test = lambda x: x

    actual_groups = consecutive_values(initial_list, comparison_test)

    assert actual_groups == expected_groups


def test_consecutive_values_end_of_list_false():
    initial_list = [True, False, False, False]

    expected_groups = [[True]]

    comparison_test = lambda x: x

    actual_groups = consecutive_values(initial_list, comparison_test)

    assert actual_groups == expected_groups
