package com.yk.system.config;

import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateDeserializer;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateSerializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.format.DateTimeFormatter;

/**
 * Jackson 全局序列化/反序列化配置
 * <p>
 * 统一将 LocalDateTime 格式设为 "yyyy-MM-dd HH:mm:ss"（前端 value-format 保持一致），
 * 将 LocalDate 格式设为 "yyyy-MM-dd"。
 * 解决前端以空格分隔的日期时间字符串无法被 Jackson 默认 ISO-8601（T 分隔符）
 * 反序列化器识别的问题。
 */
@Configuration
public class JacksonConfig {

    private static final String DATE_TIME_PATTERN = "yyyy-MM-dd HH:mm:ss";
    private static final String DATE_PATTERN = "yyyy-MM-dd";

    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonDateTimeCustomizer() {
        return builder -> builder
                .serializers(
                        new LocalDateTimeSerializer(DateTimeFormatter.ofPattern(DATE_TIME_PATTERN)),
                        new LocalDateSerializer(DateTimeFormatter.ofPattern(DATE_PATTERN))
                )
                .deserializers(
                        new LocalDateTimeDeserializer(DateTimeFormatter.ofPattern(DATE_TIME_PATTERN)),
                        new LocalDateDeserializer(DateTimeFormatter.ofPattern(DATE_PATTERN))
                );
    }
}
