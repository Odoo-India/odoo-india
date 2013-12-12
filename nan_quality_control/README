Módulo de Control de Calidad para OpenErp, actualizado a la versión 6 dónde se
han añadido alguna funcionalidad interesante. 

Este módulo es génerico , es la base para la integración  de forma automàtica
con los diferentes  modelos de la aplicación, de todas formas nos permite hacer
cualquier control de calidad a los diferentes modelos del sistema de forma
manual.  A lo largo de las siguientes semanas presentaremos otros módulos que
automatizan el control de calidad en los lotes de producción o en los
albaranes.

Definición:

* Método: Las diferentes procedimientos disponibles con los qual realizar la
prueba.
* Prueba:  El test a comprobar. Tenemos dos tipos de pruebas:
    * Cualitativas: El resultado es un descripción, color, si, No..
    * Cuantitativas: El resultado debe de estar dentro de un intervalo.
* Valores Posibles: Los valores que podemos escoger en las pruebas cualitativas.
* Sinónimos: Diferentes nombres para la misma prueba.
* Referencias en test: los diferentes modelos de la aplicación a los que se puede
pasar un test de calidad.
* Plantilla: El conjunto de pruebas  que se utilizarán en los tests!

* Una vez definidos estos valores pasamos a definir el test.

  Tenemos un *test genérico* que se podrá aplicar a cualquier modelo como por 
  ejemplo a qualquier empresa, albarán, factura o producto, o un *test
  relacionado* , haciendolo específico para un producto determinado y que se
  aplicará por ejemplo cada vez que se venda el producto o quan se cree un
  lote.

* La *fórmula* , ha sido añadido en la versión 6.0 para poder dar un resultado
al test. 

Así para definir la fórmula sólo hay que utilizar el nombre de las
líneas como operandos. Como por Ejemplo: Teniendo las 3 ĺineas de la plantilla
con nombres  A,B,C respectivamente podemos crear una formula tal que: (A*100 +B/C)*B²


Para poner un ejemplo práctico, este campo se ha utilizado en unos de nuestros
clientes que se dedica a la inseminación artificial para calcular la dosis
resultantes según los valores del test de calidad que pasa la extracción.

Una vez definidos estos parámetros sólo nos queda pasar el test.  Creamos un
nuevo test,  creamos la relación con el modelo, empresa, ventas.. , y apretamos
el botón “seleccionar plantilla”, escogemos el test y se nos rellena las ĺínieas
dependiendo de la plantilla escogida.

Ahora sólo nos queda rellenar las línieas del test. En casos que haya
diferentes métodos para una prueba sólo es necesàrio que una de las
combinaciones de prueba,método sea correcta.


Seguimos teniendo el workflow:

Borarrador -> Confirmado -> Pendiente aprovación -> Éxito
                                    |
                                    |-> Fracaso


