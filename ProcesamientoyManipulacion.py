#ESTO ES UN EJEMPLO DE USO DE GITHUB

import pandas as pd


def crear():
    d= {
        "producto": ["A", "B", "C"],
        "ventas": [100, 200, 300],
        "activo": [1, 1, 1],
        "ventas_feb": [100, 200, 300],
        "ventas_marzo": [100, 200, 300],
    }
    df = pd.DataFrame(d)
    return df


def renombrar(df: pd.DataFrame):
    df_new = df.rename(columns={"producto": "product", "ventas": "sales"})
    print(df_new)

def calcular(x):
    if x["producto"] == "A":
        return x["ventas"] * 1.08
    elif x["producto"] == "B":
        return x["ventas"] * 1.16
    else:
        return x["ventas"]

def aplicar(df: pd.DataFrame):
    #df["monto_iva"] = df["ventas"] * 1.16
    df["monto_iva"] = df.apply(calcular, axis="columns")
    print(df)


def eliminar_columnas(df: pd.DataFrame):
    eliminados = df.drop(columns=["activo"])
    print(eliminados)

# Formato ancho a formato largo
def reestructurar_datos(df: pd.DataFrame):
     res =pd.melt(df,
                  id_vars =["producto"],
                  value_vars = ["ventas", "ventas_feb", "ventas_marzo"],
                  var_name = "ventas",
                  value_name = "sales")
     print(res)
     return res

# Formato largo a formato ancho
def reestructurar_pivot(df: pd.DataFrame):
     df_ancho = df.pivot(index="producto", columns="ventas", values="sales")
     print(df_ancho)


def ordenar_valores(df: pd.DataFrame):
    df_sort = df.sort_values(by="producto", ascending=False)
    print(df_sort)

def unir_datos():
    pass


def concatenar():
    pass


if __name__ == '__main__':
    df = crear()
    renombrar(df)
    print("==============")
    aplicar(df)
    print("==============")
    eliminar_columnas(df)
    print("==============")
    res = reestructurar_datos(df)
    print("==============")
    reestructurar_pivot(res)
    print("==============")
    ordenar_valores(df)
    print("==============")
    unir_datos()
    print("==============")
    concatenar()