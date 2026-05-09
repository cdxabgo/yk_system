package com.yk.system.service;

import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class HeartRateSimulatorServiceTest {

    @Test
    void shouldRequireExplicitSimulatorEnableProperty() {
        ConditionalOnProperty annotation = HeartRateSimulatorService.class.getAnnotation(ConditionalOnProperty.class);

        assertNotNull(annotation);
        assertEquals("heart-rate.simulator", annotation.prefix());
        assertEquals(1, annotation.name().length);
        assertEquals("enabled", annotation.name()[0]);
        assertEquals("true", annotation.havingValue());
    }
}
