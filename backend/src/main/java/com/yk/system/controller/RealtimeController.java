package com.yk.system.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yk.system.common.Result;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 实时心率数据推送控制器（SSE）
 * - GET /api/realtime/stream  供前端订阅 SSE 事件流
 * - POST /api/realtime/push   供 Python ML 服务推送检测结果
 */
@RestController
@RequestMapping("/api/realtime")
public class RealtimeController {

    /** 所有在线 SSE 客户端（clientId -> SseEmitter） */
    private static final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    private static final ObjectMapper objectMapper = new ObjectMapper();

    /** SSE 连接超时设置为 0 表示永不超时（由客户端或网络断开触发 completion/error） */
    private static final long SSE_TIMEOUT = 0L;

    /**
     * 前端订阅实时数据流（SSE）
     * EventSource 不支持自定义请求头，故该接口从 Auth 拦截器中排除
     */
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        String clientId = UUID.randomUUID().toString();
        // timeout=SSE_TIMEOUT 表示永不超时（由客户端或网络断开触发 onCompletion/onError）
        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT);

        emitter.onCompletion(() -> emitters.remove(clientId));
        emitter.onTimeout(() -> {
            emitters.remove(clientId);
            emitter.complete();
        });
        emitter.onError(e -> emitters.remove(clientId));

        emitters.put(clientId, emitter);

        // 发送初始连接成功事件
        try {
            emitter.send(SseEmitter.event()
                    .name("connected")
                    .data("{\"message\":\"已连接到实时心率监测服务\",\"clientId\":\"" + clientId + "\"}"));
        } catch (IOException e) {
            emitters.remove(clientId);
        }

        return emitter;
    }

    /**
     * Python ML 服务调用此接口推送心率检测结果，由后端广播给所有订阅的前端客户端
     * 此接口仅限本机 Python 服务调用，故从 Auth 拦截器中排除
     */
    @PostMapping("/push")
    public Result<?> push(@RequestBody Map<String, Object> data, HttpServletRequest request) {
        String remoteAddr = request.getRemoteAddr();
        if (!"127.0.0.1".equals(remoteAddr) && !"0:0:0:0:0:0:0:1".equals(remoteAddr)) {
            return Result.error(403, "仅允许本机服务调用此接口");
        }
        try {
            String payload = objectMapper.writeValueAsString(data);
            // 广播给所有在线客户端，失败的连接自动移除
            emitters.entrySet().removeIf(entry -> {
                try {
                    entry.getValue().send(
                            SseEmitter.event().name("heartrate").data(payload));
                    return false;
                } catch (IOException e) {
                    return true;
                }
            });
            return Result.success();
        } catch (Exception e) {
            return Result.error("推送失败: " + e.getMessage());
        }
    }

    /**
     * 查询当前在线订阅客户端数量（可选，供调试用）
     */
    @GetMapping("/clients")
    public Result<?> clientCount() {
        return Result.success(Map.of("count", emitters.size()));
    }
}
