import type { User } from "next-auth";
import { NuxtAuthHandler } from "#auth";
import { ResponseCodesRecord } from "#shared/utils/response-codes";
import { ApiErrorSchema } from "#shared/utils/schemas/api";
import { UserResponse } from "#shared/utils/schemas/auth";
import Credentials from "next-auth/providers/credentials";
import { FetchError } from "ofetch";

const runtimeConfig = useRuntimeConfig();

export default NuxtAuthHandler({
    secret: runtimeConfig.auth.secret,
    pages: {
        newUser: "/auth/sign-up",
        signIn: "/auth/sign-in",
    },
    providers: [
        // @ts-expect-error https://auth.sidebase.io/guide/authjs/quick-start#configuration
        Credentials.default({
            id: "credentials",
            credentials: {},
            async authorize(credentials: Record<"email" | "password", string>) {
                /**
                 * Any errors that may occur inside here should be thrown
                 * using simple
                 * ```typescript
                 * throw new Error('error:code')
                 * ```
                 *
                 * and will be parsed as followed
                 * ```typescript
                 * const response = await auth.signIn('credentials')
                 * if (response.error) // do something...
                 */

                const formData = new FormData();
                formData.append("email", credentials.email);
                formData.append("password", credentials.password);

                try {
                    const response = await $fetch("/auth/sign-in", {
                        baseURL: runtimeConfig.public.apiBase,
                        method: "POST",
                        body: formData,
                    });

                    const parsedResponse = UserResponse.safeParse(response);

                    if (!parsedResponse.success) {
                        throw new Error(ResponseCodesRecord.Server.Auth.SignIn.BadPayload);
                    }

                    return {
                        id: parsedResponse.data.id,
                        name: parsedResponse.data.name,
                        email: parsedResponse.data.email,
                        role: parsedResponse.data.role,
                    } satisfies User;
                } catch (error) {
                    if (error instanceof FetchError) {
                        const parsedError = ApiErrorSchema.safeParse(error.data);
                        if (!parsedError.success) {
                            return null;
                        }

                        throw new Error(parsedError.data.error);
                    }

                    return null;
                }
            },
        }),
    ],
    jwt: {
        async encode({ secret, token, maxAge }) {
            return JWTUtils.encode(
                token,
                secret,
                runtimeConfig.auth.sign,
                maxAge || runtimeConfig.auth.maxAge,
            );
        },

        async decode({ secret, token }) {
            return JWTUtils.decode(secret, token, runtimeConfig.auth.sign);
        },
    },
    callbacks: {
        jwt({ token, user }) {
            if (user) {
                token.id = user.id;
                token.email = user.email;
                token.name = user.name;
                token.role = user.role;
            }

            return token;
        },

        async session({ session, token }) {
            if (session.user) {
                if (token.id) {
                    session.user.id = token.id;
                }

                if (token.email) {
                    session.user.email = token.email;
                }

                if (token.name) {
                    session.user.name = token.name;
                }

                if (token.role) {
                    session.user.role = token.role;
                }
            }

            session.accessToken = await JWTUtils.encode(
                token,
                runtimeConfig.auth.secret,
                runtimeConfig.auth.sign,
                runtimeConfig.auth.maxAge,
            );

            return session;
        },
    },
});
