
# Classes

## Funcionalidad de los archivos

- **admin**: En este archivo se indican los modelos y formas a las que el administrador puede accesar, modificar y crear, asi como borrar
- **forms**: En este archivo se declaran las formas que utilizan los modelos creados, con ellas es pueden crear vistas de creacion y modificacion .
- **models**: En este archivo se declaran las clases de usuarios, cursos, participaciones y asistencias, al declararlas y crear una migracion y migrar a ella, la base de datos toma esa forma con las relaciones que le indiques en models.
- **test**: Se generarn test.
- **urls.py**: En este codigo se declaran los urls dentro de classes, en este caso solo se encuentre al signup dadao que se modifico del default.

- **views**: En este archivo se generan las vistas al utilizar los htmls de la carpeta de template, este es el verdadero "backend" dado que aqui se le pasan los argumentos al fron-end para que los visualize e interactue el usuario.

