# Política de procesamiento de recetas - Clínica Demo

## Objetivo

La validación administrativa inicial tiene como objetivo
determinar si la información extraída de una receta es
suficiente para generar una orden de atención para el área
de Farmacia.

Esta validación no determina si la receta contiene todas las
instrucciones clínicas necesarias para el consumo o administración
del medicamento.

## Información necesaria para generar una orden de Farmacia

Para cada medicamento que será enviado a Farmacia deben poder
identificarse:

- nombre del medicamento;
- concentración, cuando esté indicada;
- forma farmacéutica o presentación, cuando esté indicada;
- cantidad total prescrita.

La cantidad total prescrita representa la cantidad de unidades
que Farmacia debe considerar para la atención.

El sistema no debe calcular ni inferir cantidades que no estén
explícitamente indicadas en el documento.

## Campos no obligatorios para generar la orden

Los siguientes campos no bloquean por sí solos la generación
de una orden de atención para Farmacia:

- diagnóstico;
- dosis por administración;
- frecuencia;
- duración;
- instrucciones de consumo;
- vía de administración;
- especialidad del profesional.

Estos campos pueden ser relevantes para otros procesos,
pero no son necesarios por sí solos para determinar qué
producto y cantidad debe recibir Farmacia en esta etapa.

## Campos que requieren revisión de Farmacia

La orden debe pasar a revisión cuando:

- no puede identificarse el nombre del medicamento;
- no puede identificarse la cantidad total que debe atender Farmacia;
- la información disponible no permite determinar qué producto
  debe atender Farmacia;
- existe una ambigüedad que impide determinar el medicamento,
  concentración, presentación o cantidad que corresponde a la orden.

La ausencia de frecuencia, duración o dosis por administración
no debe provocar por sí sola una revisión de Farmacia.

## Validación externa de medicamentos

La validación externa contra una fuente farmacológica autorizada
se utiliza como mecanismo complementario de corroboración y
enriquecimiento de datos.

Los posibles resultados son:

- CONFIRMED:
  la fuente externa pudo corroborar los atributos evaluados.

- NOT_CONFIRMED:
  la fuente externa no pudo corroborar suficientemente los
  atributos evaluados.

- AMBIGUOUS:
  la fuente externa encontró múltiples candidatos compatibles.

- API_ERROR:
  la fuente externa no pudo ser consultada.

CONFIRMED constituye evidencia adicional de calidad.

NOT_CONFIRMED, AMBIGUOUS y API_ERROR no bloquean por sí solos
la generación de una orden para Farmacia.

Una discrepancia externa solamente debe producir PHARMACY_REVIEW
cuando, junto con la información extraída del documento, impide
identificar suficientemente qué producto o cantidad debe atender
Farmacia.

El sistema no debe corregir automáticamente el nombre,
concentración o presentación de un medicamento basándose
únicamente en similitud con resultados de la fuente externa.

La validación externa constituye una comprobación administrativa
y de calidad de datos. No representa una decisión clínica.

## Regla sobre cantidad

La cantidad total prescrita es un dato fundamental para
generar una orden de atención de Farmacia.

No debe inferirse la cantidad utilizando:

- dosis por administración;
- frecuencia;
- duración.

Si la cantidad total no está explícitamente disponible y no puede
determinarse de manera confiable a partir del documento, la orden
debe pasar a PHARMACY_REVIEW.

## Regla sobre la información clínica

Este proceso no evalúa si el paciente recibió instrucciones
clínicas suficientes para consumir o administrar el medicamento.

Por ejemplo, la ausencia de:

- frecuencia;
- duración;
- dosis por administración;

no bloquea por sí sola una orden de atención de Farmacia.

La finalidad de este proceso es preparar una orden operacional
para Farmacia.