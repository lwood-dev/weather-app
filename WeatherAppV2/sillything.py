

def create_counter(adder):
    a = adder + adder
    def create_a_list_of_numbers(a):
        list = []
        while len(list) < a + adder:
            for n in range(a):
                list.append(n+1)
        return list
    return create_a_list_of_numbers

result_1 = create_counter(1)
result_2 = create_counter(5)
print(result_1(10), result_2(5))


while len(list) < number:
    
    list.append()