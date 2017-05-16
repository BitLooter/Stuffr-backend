"""Test data for tests to use for testing."""

import datetime


TEST_TIME = datetime.datetime(2011, 11, 11, 11, 11, 11,
                              tzinfo=datetime.timezone.utc)
TEST_TIME_COMPARE = datetime.datetime(2012, 12, 12, 12, 12, 12,
                                      tzinfo=datetime.timezone.utc)
# Generate test database
TEST_DATA = []
for u in range(2):
    user_data = {'name_first': 'User u{}'.format(u),
                 'name_last': 'User U{}'.format(u),
                 'email': 'email{}@example.com'.format(u),
                 'password': 'testing',
                 'inventories': []}
    for i in range(2):
        inventory_data = {'name': 'Test Inventory U{}I{}'.format(u, i), 'things': []}
        for t in range(2):
            ident = 'T{}'.format(t)
            thing_data = {'name': 'Test Thing U{}I{}{}'.format(u, i, ident),
                          'date_created': TEST_TIME,
                          'date_modified': TEST_TIME,
                          'location': '{} location'.format(ident),
                          'details': '{} details'.format(ident)}
            inventory_data['things'].append(thing_data)
        user_data['inventories'].append(inventory_data)
    TEST_DATA.append(user_data)
