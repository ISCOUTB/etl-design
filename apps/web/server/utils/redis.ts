import Redis from "ioredis";

export class RedisService {
    @Singleton()
    static getInstance(): Redis {
        const { database: { redis } } = useRuntimeConfig();
        return new Redis({
            host: redis.HOST,
            port: Number(redis.PORT),
            password: redis.PASSWORD,
            db: Number(redis.DB),
        });
    }
}
