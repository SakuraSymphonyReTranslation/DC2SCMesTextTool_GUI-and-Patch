namespace DC2SCMesTextTool;

/// <summary>
/// Script configuration for Da Capo II Spring Celebration (DC2SC).
/// </summary>
public class ScriptInfo
{
    public string Name { get; init; } = "";
    public ushort Version { get; init; }
    public OffsetType OffsetType { get; init; }
    
    // Opcode ranges for different instruction types
    public (byte Begin, byte End) Uint8x2 { get; init; }   // [op][arg1:byte][arg2:byte]
    public (byte Begin, byte End) Uint8Str { get; init; }  // [op][arg1:byte][string]
    public (byte Begin, byte End) String { get; init; }    // [op][string] - unencrypted
    public (byte Begin, byte End) EncStr { get; init; }    // [op][encstring] - encrypted
    public (byte Begin, byte End) Uint16x4 { get; init; }  // [op][4 x uint16]
    
    public byte EncryptionKey { get; init; }
    public byte[] OutputOpcodes { get; init; } = Array.Empty<byte>();
    
    /// <summary>
    /// Check if an opcode falls within a section range
    /// </summary>
    public bool IsInSection((byte Begin, byte End) section, byte opcode)
    {
        if (section.Begin == 0xFF && section.End == 0xFF)
            return false;
        return opcode >= section.Begin && opcode <= section.End;
    }

    /// <summary>
    /// D.C.II Spring Celebration ~Da Capo II~ configuration
    /// </summary>
    public static readonly ScriptInfo DC2SC = new()
    {
        Name = "dc2sc",
        Version = 0x3B69,
        OffsetType = OffsetType.Offset1,
        Uint8x2 = (0x00, 0x28),
        Uint8Str = (0x29, 0x2E),
        String = (0x2F, 0x49),
        EncStr = (0x4A, 0x4D),
        Uint16x4 = (0x4E, 0xFF),
        EncryptionKey = 0x20,
        OutputOpcodes = new byte[] { 0x45 }
    };

    public static readonly ScriptInfo[] AllInfos = { DC2SC };
    
    /// <summary>
    /// Query script info by name
    /// </summary>
    public static ScriptInfo? QueryByName(string name)
    {
        return AllInfos.FirstOrDefault(i => 
            i.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
    }
    
    /// <summary>
    /// Query script info from MES file data
    /// </summary>
    public static ScriptInfo? QueryFromData(byte[] data)
    {
        if (data.Length < 8)
            return null;
            
        int labelCount = BitConverter.ToInt32(data, 0);
        int offset1 = labelCount * 4 + 4;
        if (data.Length > offset1 + 2)
        {
            ushort version1 = BitConverter.ToUInt16(data, offset1);
            if (version1 == DC2SC.Version)
                return DC2SC;
        }
        
        return DC2SC;
    }
}

public enum OffsetType
{
    Offset1,  // head[0] * 4 + 4
    Offset2   // head[0] * 6 + 4
}
