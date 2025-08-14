from faker import Faker
fake = Faker('pt_BR')
print(fake.company())  # Gera uma razão social fictícia
print(fake.cnpj())     # Gera um CNPJ fictício
print(fake.date_between("-5y", "today"))  # Gera uma data entre 5 anos atrás e hoje
