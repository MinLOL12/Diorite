
package com.example.{{MOD_ID}};

import net.neoforged.fml.common.Mod;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Mod("{{MOD_ID}}")
public class ExampleMod {
    public static final String MOD_ID = "{{MOD_ID}}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public ExampleMod() {
        LOGGER.info("Hello from {{MOD_NAME}}!");
    }
}
