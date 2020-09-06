# Reto Backend Dacodes

Solución para el reto de backend de dacodes

https://bitbucket.org/dacodes/pruebas/src/master/Backend/  

## Requerimientos

1. Python 3.8
2. Django 3.1

## Descargar el proyecto
```shell
# Clonar el repositorio.
$ git clone git@bitbucket.org:dagopoot/dacodes_backend.git backend
# Nos posicionamos en la carpeta creada
$ cd backend
```

## Iniciar con docker-compose

En caso de que no tengamos instalado docker-compose, instalarlo con ayuda del manual oficial

https://docs.docker.com/compose/install/

```shell
# iniciamos el contenedor
$ sudo docker-compose up
```

## Iniciar con Conda

En caso de que no tengamos instalado Conda, instalarlo con ayuda del manual oficial

https://docs.conda.io/en/latest/miniconda.html

```shell
# creamos un nuevo ambiente con python 3.8
$ conda create --name dacodes python=3.8
# activamos el ambiente recién creado
$ conda activate dacodes
# instalamos los paquetes requeridos por el proyecto
$ pip install -r ./dacodes/requirements.txt
#iniciamos el servidor
$ python ./dacodes/manage.py runserver
```

## Unit test

### Con docker

```shell
# con el proyecto iniciado, ejecute
$ docker ps
# copie el valor del CONTAINER ID correspondiente a la imagen a continuación
CONTAINER ID     IMAGE                                       COMMAND
a1ads6dt34ad     backend_dacodes_django      "bash -c 'python man…"
# Sustituya el valor en lugar de <container-id>, este comando ejecutara las pruebas
$ docker exec -it <container-id> python /code/manage.py test dacodes
```

### Con conda

```shell
# asegúrese que esté activado el ambiente
$ conda activate dacodes
# ejecute para iniciar las pruebas
$ python ./dacodes/manage.py test dacodes
```

## Base de datos
Se incluye en el repositorio una base de datos en SQLite para propósito de la prueba

## Url de acceso a la aplicación

Una vez que inicie el proyecto en su equipo local, la siguiente dirección está disponible, esta dirección es la base para las siguientes urls que se indican en este documento.

http://localhost:8000/

## Swagger

Acceda en su navegador a la siguiente dirección para acceder a la documentación de los endpoints, esta es una herramienta que le ayuda a probar los endpoints.

```shell
/api/swagger/
```

## Registro de usuarios

En la siguiente dirección puede acceder para crear usuarios que tendrán acceso a los endpoints

```shell
/admin/
```
Cuenta de super usuario

usuario: dagopoot
contraseña: 12345

Se crearon dos grupos de usuarios **TEACHERS** y **STUDENTS**, configure sus usuarios con al menos uno de estos grupos, los endpoints validan el grupo al que pertenece el usuario.

## Endpoints

### Token

todos los endpoints requiere que se adjunte un token en el header de la petición, obtenga un token con el siguiente endpoint

```shell
POST /api/api-token-auth/
```

Proporcione el token en el header de la petición, de la forma

```shell
Authorization: Token 3de84120ec132856ee2ffcb414a07c50765f4978
```

### Endpoints para maestros

corresponden a la administración de los cursos por parte de los maestros, es necesario tener una cuenta con el grupo TEACHERS para  acceder a estos endpoints.

#### Administrar cursos

Se proporcionan todas las opciones para el desarrollo del crud de los cursos, los cursos pueden tener cursos dependientes.

```
/api/elearning/admin/courses/
```

#### Administrar lecciones

Se proporcionan todas las opciones para el desarrollo del crud de las lecciones contenidas en un curso, las lecciones pueden tener lecciones dependientes.

```
/api/elearning/admin/courses/{course_pk}/lessons/
```

#### Administrar preguntas

Se proporcionan todas las opciones para el crud de las preguntas

```
/api/elearning/admin/courses/{course_pk}/lessons/{lesson_pk}/questions/
```

Las respuestas posibles de una pregunta se deben proporcionar como parte de la petición de creación o edición, se valida que las preguntas sean de alguno de los siguientes tipos

- **BOOLEAN** se esperan dos respuestas, una de ellas correcta
- **MULTIPLE_CHOOSE_A_CORRECT_ONE** se espera al menos una respuesta correcta
- **CHOOSE_ALL_THE_RIGHT** se espera al menos una respuesta correcta

### Endpoints para estudiantes

#### Cursos disponibles

Los estudiantes obtienen todos los cursos posibles con el siguiente endpoint, se proporciona información: el estudiante está inscrito al curso,  el estudiante ya ha aprobado el curso, el estudiante a aprobado el curso dependiente.

```shell
GET /api/elearning/students/courses/
GET /api/elearning/students/courses/{course_id}/
```

#### Inscribirse a un curso

Si el curso no tiene dependientes o si ya ha aprobado el curso anterior el estudiante puede inscribirse al siguiente curso.

```shell
POST /api/elearning/students/courses/{course_id}/subscribe/
```

#### Lecciones de un curso

Obtiene el listado previo de las lecciones de un curso, se valida que el usuario esté registrado en el curso.

proporciona información adicional: el estudiante a aprobado la lección, el estudiante ha aprobado la lección dependiente.

```shell
GET /api/elearning/students/courses/{course_id}/lessons/
```

#### Contenido de la lección

Obtiene el contenido de una lección

```shell
GET /api/elearning/students/courses/{course_id}/lessons/{lesson_id}/
```

#### Obtener preguntas y respuestas para aprobar la lección

Devuelve el listado de preguntas y respuestas, se añade el tipo de pregunta.

```shell
GET /api/elearning/students/courses/{course_id}/lessons/{lesson_id}/get_test/
```

#### Enviar respuestas para su evaluación

Recibe la relación de preguntas con las respuestas de los usuarios, valida que todas las preguntas hayan sido respondidas.

Evalúa las respuestas y en caso de que sea aprobado, cambia el estatus de la lección como aprobada, de igual forma válida si ya han sido aprobadas todas las lecciones de un mismo curso, en caso afirmativo cambia el estatus del curso como aprobado.

```shell
POST /api/elearning/students/courses/{course_id}/lessons/{lesson_id}/send_test/
```

# Prueba de Logica

Solución para la prueba de logica a continuación

https://bitbucket.org/dacodes/pruebas/src/master/Logic/

## Endpoint

Se incluyo el siguiente enpoint

```shell
POST /api/elearning/logic_test
```

El endopint recibe en el body un json con el siguiente formato, correspondiente a cada uno de los escenarios: [Ver ejemplo](https://bitbucket.org/dagopoot/dacodes_backend/src/master/dacodes/elearning/fixtures/logic.json "Ver ejemplo")

Devuelve el resultado a cada escenario en el mismo orden: [Ver ejemplo de respuesta](https://bitbucket.org/dagopoot/dacodes_backend/src/master/dacodes/elearning/fixtures/logic_results.json "Ver ejemplo de respuesta")

