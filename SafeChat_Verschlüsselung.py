import random

#rest mit %??????????????????
#key-länge
#xor testen
#xor: ASCII zu Zahl machen

public_key = (31, 112) #(Primzahl, Generator) (Generator = Basis)

def DH_generate_private_key(): #wird später aus Passwort generiert?
    key = random.randint(1, 20)
    return key

def DH_calculate_change(private_key, Input = public_key[1]):
    result = (Input**private_key) % public_key[0]
    return result

def XOR_encrypt(Input, key):
    encryptet = Input ^ key # ^ ist xor
    return encryptet

def Str_encrypt(Input, key): # für jeden buchstaben ascii mit key verschlüsseln
    encryptet = []
    for i in range(len(Input)):
        encryptet.append(chr(XOR_encrypt(ord(Input[i]), key))) # ord() nimmt ASCII-Wert von char und chr macht aus Wert ein Zeichen
    return "".join(encryptet) # man kann einen string nicht bearbeiten deswegen mit liste und join


"""
# Test DH
per1 = DH_generate_private_key()
print(f"per1: {per1}\n")
per2 = DH_generate_private_key()
print(f"per2: {per2}\n")

per1change = DH_calculate_change(per1)
print(f"{per1change} per1change\n")
final_key1 = DH_calculate_change(per2, per1change)
print(f"key1: {final_key1}\n")

per2change = DH_calculate_change(per2)
print(f"{per2change} per2change\n")
final_key2 = DH_calculate_change(per1, per2change)
print(f"key2: {final_key2}\n")

# Test XOR
Input = int(input("zu verschlüsselnde Zahl eingeben: "))
Output = XOR_encrypt(Input, final_key1)
print(f"Output: {Output}")

# Test Str_encrypt
Input2 = input("zu verschlüsselnden Text eingeben: ")
Output2 = Str_encrypt(Input2, final_key1)
print(f"Output2: {Output2}")
"""