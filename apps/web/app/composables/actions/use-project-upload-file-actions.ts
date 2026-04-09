import { fileTypeFromBuffer } from "file-type";

export default function () {
    async function processFile(
        file: File,
        options: {
            supportedFormats: string[];
            mimeTypes: string[];
            onSuccess: (file: File, extension: string, mime: string) => void;
            onError: () => void;
        },
    ) {
        const bytes = new Uint8Array(await file.arrayBuffer());
        const detected = await fileTypeFromBuffer(bytes);

        const ext = (detected?.ext ?? SchemaUtils.File.getFileExtension(file.name)).toLowerCase();
        const mime = SchemaUtils.File.normalizeMime(detected?.mime ?? file.type);

        const validExt = options.supportedFormats.includes(ext);
        const validMime = !mime.length || options.mimeTypes.includes(mime);

        if (!validExt || !validMime) {
            options.onError();

            return;
        }

        options.onSuccess(file, ext, mime);
    }

    return {
        processFile,
    };
}
