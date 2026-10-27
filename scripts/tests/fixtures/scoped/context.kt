fun stored(context: Context, data: ByteArray): ByteArray = context.getSharedPreferences("p", 0).hashCode().let { data }
