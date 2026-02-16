import type { JWT } from "next-auth/jwt";
import type { Buffer } from "node:buffer";
import hkdf from "@panva/hkdf";
import { EncryptJWT, jwtDecrypt } from "jose";
import { v7 } from "uuid";

const now = () => (Date.now() / 1000) | 0;

export const JWTUtils = {
    async encode(
        token: JWT | undefined,
        secret: string | Buffer<ArrayBufferLike>,
        info: string,
        maxAge: number,
    ) {
        const encryptionSecret = await hkdf("sha256", secret, "", info, 32);

        return await new EncryptJWT(token)
            .setProtectedHeader({ alg: "dir", enc: "A256GCM" })
            .setIssuedAt()
            .setExpirationTime(now() + maxAge)
            .setJti(v7())
            .encrypt(encryptionSecret);
    },
    async decode(
        secret: string | Buffer<ArrayBufferLike>,
        token: string | undefined,
        info: string,
    ) {
        if (!token) {
            return null;
        }

        const encryptionSecret = await hkdf("sha256", secret, "", info, 32);

        const { payload } = await jwtDecrypt(token, encryptionSecret, {
            clockTolerance: 15,
        });

        return payload;
    },
};
