import numpy as np


def generate_fake_ping_data(random_state, size):
    """
    Generate random ping values (in milliseconds) between 5 and 20,
    some of them will be assigned randomly to a low latency between 100 and 200
    with direct close values between 40 and 80
    """
    values = random_state.random_integers(low=5, high=20, size=size)
    picked_low_latency_values_indexes = random_state.choice(
        size, round(0.001 * len(values)), replace=False
    )

    # Sets the picked value to a random low ping (e.g.: [100, 200]),
    # and sets the direct close values to a ping between 40 and 80ms
    for index in picked_low_latency_values_indexes:
        if index - 1 >= 0:
            values[index - 1] = random_state.random_integers(40, 80)

        values[index] = random_state.random_integers(100, 200)

        if index + 1 < size:
            values[index + 1] = random_state.random_integers(40, 80)

    return values.tolist()


def generate_fake_oco_status(random_state, size):
    """
    Generate random OCO status, mostly assigned to 200 with some 300 status codes
    during a random range between 4 and 50 ticks
    """
    values = [200] * size
    picked_error_values_indexes = random_state.choice(
        size, round(0.001 * len(values)), replace=False
    )

    for index in picked_error_values_indexes:
        values[index] = 300

        _range = range(random_state.random_integers(0, 50))

        for n in _range:
            position = index + n
            if position < size:
                values[position] = 300

    return values


def generate_fake_db_connections(random_state, size):
    """
    Generate random database connections mostly between 10 and 20 occurrences,
    assigned some ticks with a maximum connection pick up to 200
    """
    values = random_state.random_integers(low=10, high=20, size=size)
    picked_max_connections_indexes = random_state.choice(
        size, round(0.005 * len(values)), replace=False
    )

    for index in picked_max_connections_indexes:
        # Creates a linear progression between a healthy state to a bad state
        linear_values = np.arange(20, 210, 10)

        for n in range(len(linear_values) + random_state.random_integers(0, 6)):
            try:
                if n >= len(linear_values):
                    values[index + n] = 200
                else:
                    values[index + n] = linear_values[n]
            except IndexError:
                pass

    return values.tolist()


def generate_fake_http_status(random_state, size):
    """
    Generate random HTTP Status codes, mostly values will be 200,
    but some of them will be randomly assigned to a 500 during a random range between 1 and 20 ticks,
    or 0 (Curl returned value when Web sites are not reachable)
    """
    values = [200] * size
    picked_error_values_indexes = random_state.choice(
        size, round(0.0015 * len(values)), replace=False
    )
    picked_zero_values_indexes = random_state.choice(
        size, round(0.001 * len(values)), replace=False
    )

    for index in picked_zero_values_indexes:
        values[index] = 0

    for idx in picked_error_values_indexes:
        for i in range(random_state.random_integers(1, 20)):
            try:
                values[idx + i] = 500
            except IndexError:
                pass

    return values
