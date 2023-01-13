import requests
import sys
import getopt
import json
import csv
import pickle
import array
from colorama import init, Fore, Back, Style

#SCRIPT VERSION 6.0 12/08/2022


#ESTE SCRIPT REQUIERE UN FICHERO CSV EXPORTADO DE NESSUS PREFERIBLEMENTE SOLO CON LOS CAMPOS Plugin ID, Host y Plugin Output
#UNA VEZ EJECUTADO ESTE SCRIPT SOLICITARA AL USUARIO EL NOMBRE DEL ARCHIVO DONDE ESTAN LOS DATOS, NOMBRE DEL NUEVO
#FICHERO CON LOS DATOS RESULTANTE Y POR ULTIMO EL NOMBRE DE LA ORGANIZACION DE LA QUE PROVIENEN LOS DATOS
#UNA VEZ TERMINADO EL SCRIPT EL CSV RESULTANTE SE RECOMIENDA EN EXCEL/LIBREOFFICE LA COLUMNA HOST ESPECIFICAR COMO 
#TEXTO AL IMPORTAR EL .csv


#EL PRIMER IF SE ENCONTRARA EXTENSAMENTE EXPLICADO Y EN LOS POSTERIORES SE MARCARAN LAS DIFERENCIAS O COSAS POCO CLARAS

#NOMBRE DEL ARCHIVO QUE SE VA A LEER
desde = str(input(Fore.YELLOW + "Archivo a leer (sin.csv):\n------------> " + Fore.RESET))
#NOMBRE QUE SE GUARDARA PARA POSTERIOR LECTURA
para = str(input(Fore.YELLOW + "A guardar en:\n------------> " + Fore.RESET))
#ORGANIZACION DE LA QUE PROVIENE EL ESCANEO
organizacion = str(input(Fore.YELLOW + "¿Organizacion?:\n------------> " + Fore.RESET))
#ARCHIVO DE DONDE SACAR DATOS (INTRODUZCO .csv POR EXTENSION ARCHIVO)
lectura = desde + ".csv"

#ARCHIVO A DONDE GUARDAR DATOS (LO GUARDARA EN LA CARPETA resultados POR LIMPIEZA E INTRODUZCO .csv POR EXTENSION ARCHIVO)
escritura = "resultados/" + para + ".csv"
#ESTOS DOS ARRAYS SE UTILIZARAN PARA PONER SISTEMA OPERATIVO GENERICO
genericos = ["CISCO", "DARWIN", "FORTIOS", "LINUX", "VMWARE", "VXWORKS","WINDOWS"]
unix = ["UNIX", "MAC", "SOLARIS", "FREEBSD"]

#AVERIGUAMOS SI YA EXISTE UN FICHERO CON EL NOMBRE PROVISTO
try:
    file = open(escritura)
    file.close
except FileNotFoundError:
# SI NO EXISTE UN ARCHIVO CON EL NOMBRE A GUARDAR CREAMOS EL ARCHIVO Y GUARDAMOS LA CABEZERA
    cabezera = ['IP', 'HOSTNAME', 'PLUGIN', 'SISTEMA OPERATIVO','ORGANIZACION']
    with open(escritura, "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(cabezera)
# EN ESTE DICCIONARIO PYTHON GUARDAREMOS LAS IPs CON SUS CORRESPONDIENTES VALORES
valores = {}
#ABRIMOS EL ARCHIVO DESDE EL QUE SE RECIBIRAN LOS DATOS 
with open (lectura) as f:
    reader = csv.DictReader(f)
    #PARA CADA LINEA DEL CSV REALIZAMOS LAS COMPROBACIONES REQUERIDAS PARA CADA CASO CONCRETO
    for row in reader:
        #OBTENEMOS LOS DATOS QUE USAREMOS, PLUGINID LO USAREMOS PARA DIFERENCIAR LAS DISTINTAS VULS, HOST PARA IPs Y PLUGINOUTPUT PARA OBTENER LOS DATOS
        pluginid = row['Plugin ID']
        host = row['Host']
        pluginoutpost = row['Plugin Output']
        #ESTABLECEMOS LOS VALORES POR DEFECTO QUE SE INTRODUCIRAN HASTA/SI SE OBTIENEN LOS DATOS BUSCADOS
        hostname = ""
        sogenerico = "NULL"
        so = "NO ENCONTRADO"
        #EN ESTE PUNTO USAREMOS UN BUCLE ANIDADO DE IF/ELSE AL FINAL DEL MISMO SE GUARDARAN LOS VALORES POR DEFECTO EN CASO DE NO EXISTIR EN EL
        #DICCIONARIO LA IP(host)
        if pluginid == "11936":
            #EN ESTE CASO UTILIZANDO LA ESTRUCTURA DEL PLUGIN OUTPUT SEPARAREMOS EN LINEAS Y LUEGO ESPACIOS HASTA LLEGAR AL DATO
            #QUE NOS INTERESA OBTENDREMOS EL SISTEMA OPERATIVO ENTERO Y LUEGO SE DETERMINARA EL GENERICO
            separarlineas = pluginoutpost.splitlines()
            obtenerso = str(separarlineas[1])
            sogenerico = obtenerso.split(":")
            averiguar =str(sogenerico[1]).split(" ")
            encontrado = 0
            #ESTE BUCLE IF SE UTILIZARA PARA AVERIGUAR QUE SO GENERICO ES BUSCARA EN LA LISTA DE ARRIBA
            for i in averiguar:
                if i.upper() in genericos:
                    so= i.upper()
                    encontrado = 1
                    break
                else:
                    if i.upper() in unix:
                        so = "UNIX"
                        encontrado = 1
                        break
            #SI NO ES ENCONTRADO EN LA LISTA SE INTRODUCIRA "OTROS"
            if encontrado == 0:
                so = "OTROS"
            #BUSCO SI EXISTEN DATOS YA EXISTENTES EN EL DICCIONARIO SI ES ASI SOLO ACTUALIZARE LA COLUMNA "SISTEMA OPERATIVO"
            if host in valores.keys():
                temporal = valores.get(host)
                temporal[2] = sogenerico[1]
                temporal[3] = so
                valores.update({host: temporal})
            else:
                valores.update({host: [host,hostname,sogenerico[1],so,organizacion]})

        else:
            if pluginid == "50350":
                #SI DETECTO ESTE PLUGIN ES QUE NO SE HA PODIDO DETECTAR EL SISTEMA OPERATIVO
                #PROCEDO A GUARDAR LOS VALORES DEFINIDOS ABAJO
                if host in valores.keys():
                    temporal = valores.get(host)
                    temporal[2] = "NO IDENTIFICADO"
                    temporal[3] = "FALLO IDENTIFICACION"
                    valores.update({host: temporal})
                else:
                    valores.update({host: [host,hostname,"NO IDENTIFICADO","FALLO IDENTIFICACION",organizacion]})
            else:
                #EN ESTA PARTE, SE REPETIRA EN CADA SCRIPT, SIRVE PARA OBTENER HOSTNAMES SI TIENE/NESSUS LOGRA ENCONTRARLO
                #Host Fully Qualified Domain Name (FQDN) Resolution
                if pluginid == "12053":
                    #EN ESTE TROZO VOY HACIENDO .split PARA IR SEPARANDO LOS DATOS QUE ME INTERESAN Y OBTENER EL HOSTNAME
                    dato = pluginoutpost.split(' ')
                    filtro1 = dato[3]
                    filtro2 = filtro1.split('.\n')
                    hostname = filtro2[0]
                    if host in valores.keys():
                        temporal = valores.get(host)
                        if temporal[1] == "":
                            temporal[1] = hostname
                        else:
                            temporal[1] += "-" + pluginoutpost
                        valores.update({host: temporal})
                    else:
                        valores.update({host: [host,hostname,so,sogenerico,organizacion]})
                else:
                    #Additional DNS Hostnames
                    if pluginid == "46180":
                    #EN ESTE TROZO VOY HACIENDO .split PARA IR SEPARANDO LOS DATOS QUE ME INTERESAN Y OBTENER EL HOSTNAME
                        dato = pluginoutpost.split(' ')
                        filtro1 = dato[11]
                        filtro2 = filtro1.split('\n')
                        hostname = filtro2[0]
                        if host in valores.keys():
                            temporal = valores.get(host)
                            if temporal[1] == "":
                                temporal[1] = hostname
                            else:
                                temporal[1] += "-" + hostname
                            valores.update({host: temporal})
                        else:
                            valores.update({host: [host,hostname,so,sogenerico,organizacion]})
                    else:
                        #LLEGADOS A ESTE PUNTO LO QUE ME INTERESA ES SI LA IP SE ENCUENTRA DENTRO DEL DICCIONARIO
                        #SI ES ASI NO SE HACE NADA, EN CASO CONTRARIO PROCEDO A INTRODUCIR LA IP
                        #EN EL DICCIONARIO, ES UNA FORMA DE ASEGURARSE DE QUE GUARDO TODAS LAS IPs EXISTENTES
                        #EN EL FICHERO
                        if host not in valores.keys():
                            valores.update({host: [host,hostname,so,sogenerico,organizacion]})

#UNA VEZ RECORRIDO POR COMPLETO EL ARCHIVO DEL QUE SE OBTIENEN LOS DATOS PROCEDEMOS A GUARDAR LA INFORMACION DEL
#DICCIONARIO EN UN FICHERO .csv
for clave in valores:
    valor = valores.get(clave)
    with open(escritura, "a") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(valor)
#PARA INDICAR FINALIZACION  LOS Fore. SIRVEN PARA CAMBIAR EL COLOR DEL TEXTO PRESENTE EN EL TERMINAL
print(Fore.YELLOW + "Script para sacar SISTEMA OPERATIVO finalizado consultalo en " + Fore.RESET + Fore.BLUE + escritura +Fore.RESET)