/*
 * system_stm32f4xx.c
 *
 *  Created on: May 24, 2026
 *      Author: sanjeevreddyvelagala
 */

#include <stdint.h>

//set default clock speed here MANUALLY
uint32_t SystemCoreClock = 16000000;

const uint8_t APBPrescTable[8] = {0, 0, 0, 0, 1, 2, 3, 4};
const uint8_t AHBPrescTable[16] = {0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 1, 2, 3, 4 , 5 , 6 , 7 , 8};
