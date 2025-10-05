"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect } from "react";

// Validation schema
const conversationSchema = z.object({
  title: z.string().min(1, "Título é obrigatório").max(255, "Título muito longo"),
  ai_provider: z.enum(["openai", "anthropic", "gemini", "grok"]),
  ai_model: z.string().min(1, "Modelo é obrigatório"),
  system_prompt: z.string().optional(),
});

type ConversationFormData = z.infer<typeof conversationSchema>;

// Model options by provider
const MODEL_OPTIONS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "gpt-4o-mini", label: "GPT-4o Mini" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  ],
  anthropic: [
    { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
    { value: "claude-3-opus-20240229", label: "Claude 3 Opus" },
    { value: "claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
    { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
  ],
  gemini: [
    { value: "gemini-2.0-flash-exp", label: "Gemini 2.0 Flash" },
    { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" },
    { value: "gemini-1.5-flash", label: "Gemini 1.5 Flash" },
  ],
  grok: [
    { value: "grok-beta", label: "Grok Beta" },
    { value: "grok-vision-beta", label: "Grok Vision Beta" },
  ],
};

interface NewConversationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ConversationFormData) => Promise<void>;
  isSubmitting?: boolean;
}

export function NewConversationModal({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting = false,
}: NewConversationModalProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ConversationFormData>({
    resolver: zodResolver(conversationSchema),
    defaultValues: {
      title: "",
      ai_provider: "openai",
      ai_model: "gpt-4o",
      system_prompt: "",
    },
  });

  const selectedProvider = watch("ai_provider");

  // Update model when provider changes
  useEffect(() => {
    if (selectedProvider) {
      const firstModel = MODEL_OPTIONS[selectedProvider]?.[0]?.value;
      if (firstModel) {
        setValue("ai_model", firstModel);
      }
    }
  }, [selectedProvider, setValue]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset();
    }
  }, [isOpen, reset]);

  const handleFormSubmit = async (data: ConversationFormData) => {
    await onSubmit(data);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Nova Conversa</h2>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(handleFormSubmit)} className="p-6 space-y-4">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Título <span className="text-red-500">*</span>
            </label>
            <input
              {...register("title")}
              id="title"
              type="text"
              placeholder="Ex: Ajuda com Python"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
          </div>

          {/* Provider */}
          <div>
            <label htmlFor="ai_provider" className="block text-sm font-medium text-gray-700 mb-1">
              Provedor de IA <span className="text-red-500">*</span>
            </label>
            <select
              {...register("ai_provider")}
              id="ai_provider"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Google Gemini</option>
              <option value="grok">xAI Grok</option>
            </select>
            {errors.ai_provider && (
              <p className="mt-1 text-sm text-red-600">{errors.ai_provider.message}</p>
            )}
          </div>

          {/* Model */}
          <div>
            <label htmlFor="ai_model" className="block text-sm font-medium text-gray-700 mb-1">
              Modelo <span className="text-red-500">*</span>
            </label>
            <select
              {...register("ai_model")}
              id="ai_model"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {MODEL_OPTIONS[selectedProvider]?.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
            {errors.ai_model && (
              <p className="mt-1 text-sm text-red-600">{errors.ai_model.message}</p>
            )}
          </div>

          {/* System Prompt */}
          <div>
            <label
              htmlFor="system_prompt"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Prompt do Sistema (opcional)
            </label>
            <textarea
              {...register("system_prompt")}
              id="system_prompt"
              rows={4}
              placeholder="Ex: Você é um assistente especializado em programação Python..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <p className="mt-1 text-xs text-gray-500">
              Define o comportamento e personalidade da IA
            </p>
            {errors.system_prompt && (
              <p className="mt-1 text-sm text-red-600">{errors.system_prompt.message}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSubmitting ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Criando...
                </>
              ) : (
                "Criar Conversa"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
