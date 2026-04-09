import type { ResponseProjectSchema } from "#shared/utils/schemas/api";
import type { z } from "zod";
import { faker } from "@faker-js/faker";

export function mockResponseProjectSchema(id: number): z.infer<typeof ResponseProjectSchema> {
    return {
        id: faker.string.uuid(),
        name: `Mock Project ${id}`,
        description: faker.lorem.sentence(),
        provider: faker.string.sample({ min: 3, max: 7 }),
        db_host: faker.internet.ip(),
        db_port: faker.number.int({ min: 1024, max: 65535 }),
        db_user: faker.internet.username(),
        db_password: null,
        db_name: faker.string.sample({ min: 3, max: 10 }),
        db_params: null,
        created_at: faker.date.past().toISOString(),
        updated_at: faker.date.recent().toISOString(),
    };
}
