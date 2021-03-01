def find(elem, vett):
    cont = 0
    return (cont = cont + 1 for el in vett if elem == el)


if __name__ == '__main__':
    vett = ["ciao","miao","pino"]
    elem = "ciao"
    if find(elem,vett) is True:
        print("ok")
    else:
        print("no")